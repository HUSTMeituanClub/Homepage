Title: Android 消息机制（三）Native层消息机制
Date: 2017-11-02 15:57:53
Category: Android
Tags: android, event
Authors: Di Wu


之前的两篇文章讲解了`java`层消息机制的过程以及使用，中间省略了比较多的代码就是在`native`层实现的消息机制中使用的。这篇文章就对这一部分进行讲解。

## 起点

我们从第一篇文章知道，`Looper.loop()`方法被调用后，会启动一个无限循环，而在这个循环中，调用了`MessageQueue`的`next()`方法以获取下一条消息，而`next()`方法中会首先调用`nativePollOnce()`方法，这个方法的作用在之前说过是阻塞，达到超时时间或有新的消息到达时得到`eventFd`的通知再唤醒消息队列，其实这个方法也是`native`消息处理的开始。

## 进入Native层

### android_os_MessageQueue_nativePollOnce()

```c++
static void android_os_MessageQueue_nativePollOnce(JNIEnv* env, jobject obj,
        jlong ptr, jint timeoutMillis) {
    NativeMessageQueue* nativeMessageQueue = reinterpret_cast<NativeMessageQueue*>(ptr);
    nativeMessageQueue->pollOnce(env, obj, timeoutMillis);
}
```

```c++
void NativeMessageQueue::pollOnce(JNIEnv* env, jobject pollObj, int timeoutMillis) {
    mPollEnv = env;
    mPollObj = pollObj;
    mLooper->pollOnce(timeoutMillis);
    mPollObj = NULL;
    mPollEnv = NULL;
  	...
}
```

调用了`Native Looper`的`pollOnce()`方法：

### pollOnce()

```c++
inline int pollOnce(int timeoutMillis) {
	return pollOnce(timeoutMillis, NULL, NULL, NULL);
}
```

```c++
int Looper::pollOnce(int timeoutMillis, int* outFd, int* outEvents, void** outData) {
    int result = 0;
    for (;;) {
        while (mResponseIndex < mResponses.size()) {
            const Response& response = mResponses.itemAt(mResponseIndex++);
            int ident = response.request.ident;
            if (ident >= 0) {
                int fd = response.request.fd;
                int events = response.events;
                void* data = response.request.data;
              
                if (outFd != NULL) *outFd = fd;
                if (outEvents != NULL) *outEvents = events;
                if (outData != NULL) *outData = data;
                return ident;
            }
        }

        if (result != 0) {
            if (outFd != NULL) *outFd = 0;
            if (outEvents != NULL) *outEvents = 0;
            if (outData != NULL) *outData = NULL;
            return result;
        }

        result = pollInner(timeoutMillis);
    }
}
```

我们之前直接跳过了26行之前的内容，现在我们还是不能理解这一段的意义，从程序上看，我们从`mResponse`容器中取出了一个`response`并把他的内容放入了传入的地址参数中返回。首先，这个调用中没有传入地址参数，其次，这个`mResponse`数组是什么呢？

我们继续先往下看，下面的`pollInner()`方法比较长也是`native`消息机制的核心，我们拆成几个部分看。

## pollInner()

### Request 与 Response

```c++
    int result = POLL_WAKE;
    mResponses.clear();
    mResponseIndex = 0;
    mPolling = true;

    struct epoll_event eventItems[EPOLL_MAX_EVENTS];
    int eventCount = epoll_wait(mEpollFd, eventItems, EPOLL_MAX_EVENTS, timeoutMillis);
    mPolling = false;
    mLock.lock();
	...
    for (int i = 0; i < eventCount; i++) {
        int fd = eventItems[i].data.fd;
        uint32_t epollEvents = eventItems[i].events;
        if (fd == mWakeEventFd) {
            if (epollEvents & EPOLLIN) {
                awoken();
            } else {
                ALOGW("Ignoring unexpected epoll events 0x%x on wake event fd.", epollEvents);
            }
        } else {
            ssize_t requestIndex = mRequests.indexOfKey(fd);
            if (requestIndex >= 0) {
                int events = 0;
                if (epollEvents & EPOLLIN) events |= EVENT_INPUT;
                if (epollEvents & EPOLLOUT) events |= EVENT_OUTPUT;
                if (epollEvents & EPOLLERR) events |= EVENT_ERROR;
                if (epollEvents & EPOLLHUP) events |= EVENT_HANGUP;
                pushResponse(events, mRequests.valueAt(requestIndex));
            } else {
                ALOGW("Ignoring unexpected epoll events 0x%x on fd %d that is "
                        "no longer registered.", epollEvents, fd);
            }
        }
    }
```

当第7行系统调用`epoll_wait()`返回时，说明因注册的`fd`有消息或达到超时，在第11行就对收到的唤醒`events`进行遍历，首先判断有消息的`fd`是不是用于唤醒的`mWakeEventFd`，如果不是的话，说明是系统调用`addFd()`方法设置的自定义`fd`（后面会讲）。那么我们需要对这个事件作出响应。

第21到28行就对这个`event`做处理，首先，我们以这个`fd`为`key`从`mRequests`中找到他的索引，这个`mRequests`是我们在`addFd()`方法一并注册的以`fd`为`key`，`Request`为`value`的映射表。找到`request`之后，28行调用`pushResponse()`方法去建立`response`：

```c++
void Looper::pushResponse(int events, const Request& request) {
    Response response;
    response.events = events;
    response.request = request;
    mResponses.push(response);
}
```

现在我们要处理的任务已经被封装成了一个`Response`对象，等待被处理，那么真正的处理在哪里呢？

在上面的代码与处理`response`的代码中间夹着的是处理`MessageEnvelope`的代码，我们后面再讲这段，现在到处理`response`的代码：

```c++
    for (size_t i = 0; i < mResponses.size(); i++) {
        Response& response = mResponses.editItemAt(i);
        if (response.request.ident == POLL_CALLBACK) {
            int fd = response.request.fd;
            int events = response.events;
            void* data = response.request.data;
            int callbackResult = response.request.callback->handleEvent(fd, events, data);
            if (callbackResult == 0) {
                removeFd(fd, response.request.seq);
            }
            response.request.callback.clear();
            result = POLL_CALLBACK;
        }
    }
```

遍历所有`response`对象，取出之前注册的`request`对象的信息，然后调用了`request.callback->handleEvent()`方法进行回调，如果该回调返回0，则调用`removeFd()`方法取消这个`fd`的注册。

再梳理一遍这个过程：注册的自定义`fd`被消息唤醒，从`mRequests`中以`fd`为`key`找到对应的注册好的`request`对象然后生成`response`对象，在`MessageEnvelop`处理完毕之后处理`response`，调用`request`中的`callback`的`handleEvent()`方法。

那么`addFd()`注册自定义`fd`与`removeFd()`取消注册是如何实现的呢？

#### addFd()

```c++
int Looper::addFd(int fd, int ident, int events, const sp<LooperCallback>& callback, void* data) {
	...
    { // acquire lock
        AutoMutex _l(mLock);

        Request request;
        request.fd = fd;
        request.ident = ident;
        request.events = events;
        request.seq = mNextRequestSeq++;
        request.callback = callback;
        request.data = data;
        if (mNextRequestSeq == -1) mNextRequestSeq = 0; // reserve sequence number -1

        struct epoll_event eventItem;
        request.initEventItem(&eventItem);

        ssize_t requestIndex = mRequests.indexOfKey(fd);
        if (requestIndex < 0) {
            int epollResult = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, fd, & eventItem);
            if (epollResult < 0) {
                ALOGE("Error adding epoll events for fd %d: %s", fd, strerror(errno));
                return -1;
            }
            mRequests.add(fd, request);
        } else {
            int epollResult = epoll_ctl(mEpollFd, EPOLL_CTL_MOD, fd, & eventItem);
            if (epollResult < 0) {
                if (errno == ENOENT) {
                    epollResult = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, fd, & eventItem);
                    if (epollResult < 0) {
                        ALOGE("Error modifying or adding epoll events for fd %d: %s",
                                fd, strerror(errno));
                        return -1;
                    }
                    scheduleEpollRebuildLocked();
                } else {
                    ALOGE("Error modifying epoll events for fd %d: %s", fd, strerror(errno));
                    return -1;
                }
            }
            mRequests.replaceValueAt(requestIndex, request);
        }
    } // release lock
    return 1;
}
```

第6-13行使用传入的参数初始化了`request`对象，然后16行由`request`来初始化注册`epoll`使用的`event`。19行根据`mRequests.indexOfKey()`方法取出的值来判断`fd`是否已经注册，如果未注册，则在20行进行系统调用`epoll_ctl()`注册新监听并在25行将`fd`与`request`存入`mRequest`，如果已注册，则在27行更新注册并在42行更新`request`。

这就是自定义`fd`设置的过程：保存`request`并使用`epoll_ctl`系统调用注册`fd`的监听。

#### removeFd()

```c++
int Looper::removeFd(int fd, int seq) {
    { // acquire lock
        AutoMutex _l(mLock);
        ssize_t requestIndex = mRequests.indexOfKey(fd);
        if (requestIndex < 0) {
            return 0;
        }
        if (seq != -1 && mRequests.valueAt(requestIndex).seq != seq) {
            return 0;
        }
        mRequests.removeItemsAt(requestIndex);

        int epollResult = epoll_ctl(mEpollFd, EPOLL_CTL_DEL, fd, NULL);
        if (epollResult < 0) {
            if (seq != -1 && (errno == EBADF || errno == ENOENT)) {
                scheduleEpollRebuildLocked();
            } else {
                ALOGE("Error removing epoll events for fd %d: %s", fd, strerror(errno));
                scheduleEpollRebuildLocked();
                return -1;
            }
        }
    } // release lock
    return 1;
}
```

解除的过程相反，在第11行删除`mRequests`中的键值对，然后在第13行系统调用`epoll_ctl()`解除`fd`的`epoll`注册。

### MessageEnvelop消息处理

之前说到，在`request`生成`response`到`response`的处理中间有一段代码执行了`MessageEnvelop`消息的处理，这个顺序保证了`MessageEnvelop`优先于`fd`引起的`request`的处理。

现在我们来看这段代码：

```c++
    mNextMessageUptime = LLONG_MAX;
    while (mMessageEnvelopes.size() != 0) {
        nsecs_t now = systemTime(SYSTEM_TIME_MONOTONIC);
        const MessageEnvelope& messageEnvelope = mMessageEnvelopes.itemAt(0);
        if (messageEnvelope.uptime <= now) {
            { // obtain handler
                sp<MessageHandler> handler = messageEnvelope.handler;
                Message message = messageEnvelope.message;
                mMessageEnvelopes.removeAt(0);
                mSendingMessage = true;
                mLock.unlock();
                handler->handleMessage(message);
            } // release handler

            mLock.lock();
            mSendingMessage = false;
            result = POLL_CALLBACK;
        } else {
            mNextMessageUptime = messageEnvelope.uptime;
            break;
        }
    }
```

可以看到`mMessageEnvelopes`容器中存储了所有的消息，第4行从首位置取出一条消息，随后进行时间判断，如果时间到达，先移出容器，与`java`层比较相似都是调用了`handler`的`handleMessage()`来进行消息的处理。

那么`MessageEnvelope`是如何添加的呢？

`Native Looper`提供了一套与`java`层`MessageQueue`类似的方法，用于添加`MessageEnvelope`：

```c++
void Looper::sendMessageAtTime(nsecs_t uptime, const sp<MessageHandler>& handler,
        const Message& message) {
    size_t i = 0;
    { // acquire lock
        AutoMutex _l(mLock);

        size_t messageCount = mMessageEnvelopes.size();
        while (i < messageCount && uptime >= mMessageEnvelopes.itemAt(i).uptime) {
            i += 1;
        }

        MessageEnvelope messageEnvelope(uptime, handler, message);
        mMessageEnvelopes.insertAt(messageEnvelope, i, 1);

        if (mSendingMessage) {
            return;
        }
    } // release lock
    if (i == 0) {
        wake();
    }
}
```

这段添加`MessageEnvelope`的代码不需要太多的解释。

## 小结

现在我们看到，其实`Native`中的消息机制有两个方面，一方面是通过`addFd()`注册的自定义`fd`触发消息处理，通过`mRequests`保存的`request`对象中的`callback`进行消息处理。另一方面是通过与`java`层类似的`MessageEnvelop`消息对象进行处理，调用的是该对象`handler`域的`handleMessage()`方法，与`java`层非常类似。优先级是先处理`MessageEnvelop`再处理`request`。

## 一些思考

现在消息机制全部内容分析下来，我们可以看到`android`的消息机制不算复杂，分为`native`与`java`两个部分，这两个部分分别有自己的消息处理机制，其中关键的超时与唤醒部分是借助了`linux`系统`epoll`机制来实现的。

连接`java`与`native`层消息处理过程的是`next()`方法中的`nativePollOnce()`，`java`层消息循环先调用它，自身阻塞，进入`native`的消息处理，在`native`消息处理完毕后返回，再进行`java`层的消息处理，正是因为如此，如果我们在处理`java`层消息的时候执行了耗时或阻塞的任务（甚至阻塞了整个主线程），整个`java`层的消息循环就会阻塞，也无法进入`native`层的消息处理，也就无法响应例如触摸事件这样的消息，导致ANR的发生。这也就是我们不应在主线程中执行这类任务的原因。
