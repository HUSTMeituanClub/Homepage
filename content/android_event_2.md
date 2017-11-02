Title: Android 消息机制（二）Handler对消息机制的使用
Date: 2017-10-24 17:03:43
Category: Android
Tags: android, event
Authors: Di Wu


[Android 消息机制（一）消息队列的创建与循环的开始 Looper与MessageQueue](http://www.viseator.com/2017/10/22/android_event_1/)中讲述了消息机制的底层实现，下面就从平时所常用的`Handler`来讲述消息机制的使用。

## Handler

`Handler`是我们平时进行异步、多线程开发中常用的一个组件，如果在应用主线程中调用阻塞的或者资源消耗量大的任务，会造成UI的更新卡顿，所以我们会将这样的任务放在新的线程中进行操作。当需要通知UI进行更新时，我们会使用`Handler`创建消息丢入主线程的消息队列，再等待主线程的`Handler`的处理方法随着消息的处理而被调用，再进行下面的操作。这是`Handler`的基本用法，它的实现就与消息机制密切相关。

下面我们就对它的实现进行分析。

<!--more-->

### 构造

`Handler`的构造方法中除了实现默认参数的相互调用外，有内容的有这么两个：

```java
public Handler(Callback callback, boolean async) {
    ...
    mLooper = Looper.myLooper();
    if (mLooper == null) {
        throw new RuntimeException(
            "Can't create handler inside thread that has not called Looper.prepare()");
    }
    mQueue = mLooper.mQueue;
    mCallback = callback;
    mAsynchronous = async;
}
```

如果传入的了`callback`，将会保存到`mCallback`域中，之后的消息处理中会看到。

如果没有传入`loop`参数，将会使用默认的`Looper.myLooper()`也就是之前提到过的本线程`TLS`中储存的`Looper`对象。`mQueue`消息队列就是从该`Looper`中获取的消息队列。

```java
public Handler(Looper looper, Callback callback, boolean async) {
    mLooper = looper;
    mQueue = looper.mQueue;
    mCallback = callback;
    mAsynchronous = async;
}
```

如果传入了`looper`，那么我们将从它这里获取对应的消息队列对象，之后的消息就会放入这个队列中，这也是我们可以通过`Handler`实现跨线程通信的基础。

### 发送消息

#### sendMessage调用链

那么我们直接进入主题：使用`Handler`来发送异步处理的消息。

发送消息，我们最常用的是`sendMessage()`方法：

```java
public final boolean sendMessage(Message msg)
{
    return sendMessageDelayed(msg, 0);
}
```

```java
public final boolean sendMessageDelayed(Message msg, long delayMillis)
{
    if (delayMillis < 0) {
        delayMillis = 0;
    }
    return sendMessageAtTime(msg, SystemClock.uptimeMillis() + delayMillis);
}
```

```java
public boolean sendMessageAtTime(Message msg, long uptimeMillis) {
    MessageQueue queue = mQueue;
    if (queue == null) {
        RuntimeException e = new RuntimeException(
                this + " sendMessageAtTime() called with no mQueue");
        Log.w("Looper", e.getMessage(), e);
        return false;
    }
    return enqueueMessage(queue, msg, uptimeMillis);
}
```

最终调用的是`sendMessageAtTime()`方法，发送在特定时刻处理的消息。

然后调用`enqueueMessage()`方法：

```java
private boolean enqueueMessage(MessageQueue queue, Message msg, long uptimeMillis) {
    msg.target = this;
    if (mAsynchronous) {
        msg.setAsynchronous(true);
    }
    return queue.enqueueMessage(msg, uptimeMillis);
}
```
这里的第2行中，将`msg`的`target`设置为`this`也就是这个`Handler`本身，我们回想起消息循环中处理`Message`的调用：
```java
msg.target.dispatchMessage(msg);
```
现在我们知道，`Handler`发送的消息被消息队列拿到后，会调用发送它的`Handler`的`dispatchMessage()`方法对它进行处理。

然后，调用了`MessageQueue`的`enqueueMessage()`方法来向消息队列中插入消息：

#### enqueueMessage

```java
boolean enqueueMessage(Message msg, long when) {
    // 不允许没有target的Message，这种Message(barrier)只能由系统产生用于唤醒消息队列
    if (msg.target == null) {
        throw new IllegalArgumentException("Message must have a target.");
    }
    // 防止消息被重复处理
    if (msg.isInUse()) {
        throw new IllegalStateException(msg + " This message is already in use.");
    }

    synchronized (this) {
        // 检查消息队列是否处于退出状态
        if (mQuitting) {
            IllegalStateException e = new IllegalStateException(
                    msg.target + " sending message to a Handler on a dead thread");
            Log.w(TAG, e.getMessage(), e);
            msg.recycle();
            return false;
        }

        msg.markInUse();
        msg.when = when;
        Message p = mMessages;
        boolean needWake;
        if (p == null || when == 0 || when < p.when) {
            // 在这三种情况下，这条消息被插入到了队列的头部，因此我们应唤醒消息队列
            msg.next = p;
            mMessages = msg;
            needWake = mBlocked; // 如果处于阻塞状态，则需要进行唤醒
        } else {
            // 在队列中插入的消息，只有在target为空（barrier）并且设置为异步时，需要进行唤醒操作
            needWake = mBlocked && p.target == null && msg.isAsynchronous();
            Message prev;
            // 熟悉的链表插入操作
            for (;;) {
                prev = p;
                p = p.next;
                if (p == null || when < p.when) {
                    break；
                }
                if (needWake && p.isAsynchronous()) {
                    needWake = false; // 如果有消息不需要进行异步处理，则无需进行唤醒操作
                }
            }
            // 插入到p结节之前
            msg.next = p; 
            prev.next = msg;
        }
        // 如果有needWake标记，则进行消息队列的唤醒操作
        if (needWake) {
            nativeWake(mPtr);
        }
    }
    return true;
}
```

整个方法的流程在注释中进行了分析，这里主要就分为了两种情况，需要进行队列唤醒与无需进行队列唤醒的，如果需要队列唤醒操作（有`needWake`标记），则会在调用的最后调用`nativeWake()`方法进行`native`的唤醒操作。

#### 队列的唤醒

```c++
static void android_os_MessageQueue_nativeWake(JNIEnv* env, jclass clazz, jlong ptr) {
    NativeMessageQueue* nativeMessageQueue = reinterpret_cast<NativeMessageQueue*>(ptr);
    nativeMessageQueue->wake();
}
```

`native`方法中，利用`mPtr`指针找到`native`层创建的`NativeMessageQueue`对象，然后调用了它的`wake()`方法：

```c++
void NativeMessageQueue::wake() {
    mLooper->wake();
}
```

而接着调用的是`NativeMessageQueue`对象的中保存的`Native Looper`对象的`wake()`方法：

```c++
void Looper::wake() {
    uint64_t inc = 1;
    ssize_t nWrite = TEMP_FAILURE_RETRY(write(mWakeEventFd, &inc, sizeof(uint64_t)));
    if (nWrite != sizeof(uint64_t)) {
        if (errno != EAGAIN) {
            LOG_ALWAYS_FATAL("Could not write wake signal to fd %d: %s",
                    mWakeEventFd, strerror(errno));
        }
    }
}
```

这个方法做的事情非常简单，利用`write()`函数，向`mWakeEventFd`这个`fd`中写入了`inc`这个值（1）。

为什么只需要这样简单的写入就可以做到唤醒消息队列呢？

我们再回想到上一篇文章中的`Native Looper`创建与`Epoll`的初始化过程，我们创建了这个`eventFd`类型的`mWakeEventFd`，并且为它注册了`epoll`监听，一旦有来自于`mWakeEventFd`的新内容，`NativePollOnce()`中的`epoll_wait()`调用就会返回，这里就已经起到了唤醒队列的作用。

到这里，发送（插入）新消息到消息队列的过程已经完成，我们只需要等待设置的时间到达，消息队列就会取出我们发送的消息并进行处理。

### 消息的处理

消息队列拿到消息后，调用`msg.target.dispatchMessage(msg);`进行消息的处理，从前文我们了解到，`Handler`发送的消息的`target`就是`Handler`自身，所以调用的就是它的`dispatchMessage()`方法：

```java
public void dispatchMessage(Message msg) {
    if (msg.callback != null) {
        handleCallback(msg);
    } else {
        if (mCallback != null) {
            if (mCallback.handleMessage(msg)) {
                return;
            }
        }
        handleMessage(msg);
    }
}
```

这个过程也比较经典，第2行`if`判断`Message`是否拥有自己的`callback`，如果有的话就调用`handleCallback()`来运行这个`Runnable`：

```java
private static void handleCallback(Message message) {
    message.callback.run();
}
```

如果没有自带`callback`，第5行检查`Handler`是否自带`callback`，如果有的话就去执行这个`callback`，但是这里还有一点细节需要注意，如果这个方法返回了`false`，那么后面`Handler`自带的`handlerMessage()`方法同样会被执行，这里其实就是一个执行的优先级顺序的问题，一般情况下我们使用时只会传入`callback`或是重写`Handler`的`handleMessage()`方法，优先级也就是确保一个执行顺序的逻辑。

---

到这里，`Handler`的部分就结束了，但是整个消息机制的分析还没有结束，到现在我们分析的都是`java`层对消息的处理过程，略过了`native`层自己的一套处理来自于`native`的消息的机制，下面一篇文章就会把关注点放在这一部分。
