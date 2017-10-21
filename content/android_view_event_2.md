Title: Android 触摸事件分发机制（二）原始事件消息传递与分发的开始
Date: 2017-10-7 13:00:00
Category: Android
Tags: android, view 
Authors: Di Wu

## 回顾

在[上一篇文章](http://www.viseator.com/2017/09/14/android_view_event_1/)中，我们探索了从内核触摸事件传递到`InputDispatcher`线程，再与应用线程之间建立`InputChannel`的过程，并且我们已经看到一个最原始的触摸事件被封装成一个`msg`并通过`InputChannel`建立的`socket`通过`sendMessage()`方法跨线程通信发送给了应用的UI线程。

这篇文章将会看到应用UI线程的消息队列是如何读取传递过来的触摸事件并进行处理、分发的。

<!--more-->

本篇文章主要参考了[Gityuan的文章](http://gityuan.com/2016/12/31/input-ipc/)

## 消息循环

`Android`的消息机制的具体内容在这里不详细叙述：

每个线程都可以拥有一个自己的消息队列与一个`Looper`，在`Looper`初始化的过程中，会启动一个循环来不断读取、处理队列中的消息，`Android`是一个事件驱动的模型，只有源源不断的事件产生与处理才能推动应用的进行。

同时应该注意的是在`Java`与`Native`中各有一套消息处理的流程可以进行消息的处理。

### Looper

当应用初始化时，会调用`Looper.prepare()`：

```java
private static void prepare(boolean quitAllowed) {
    if (sThreadLocal.get() != null) {
        throw new RuntimeException("Only one Looper may be created per thread");
    }
    sThreadLocal.set(new Looper(quitAllowed));
}
```

会在`ThreadLocal`区域新建一个`Looper`对象：

```java
private Looper(boolean quitAllowed) {
    mQueue = new MessageQueue(quitAllowed);
    mThread = Thread.currentThread();
}
```

同时初始化了一个`MessageQueue`，保存了当前的线程：

```java
MessageQueue(boolean quitAllowed) {
    mQuitAllowed = quitAllowed;
    mPtr = nativeInit();
}
```

`nativeInit()`方法初始化了`native`的消息队列：

```c++
static jlong android_os_MessageQueue_nativeInit(JNIEnv* env, jclass clazz) {
    NativeMessageQueue* nativeMessageQueue = new NativeMessageQueue();
    if (!nativeMessageQueue) {
        jniThrowRuntimeException(env, "Unable to allocate native queue");
        return 0;
    }

    nativeMessageQueue->incStrong(env);
    return reinterpret_cast<jlong>(nativeMessageQueue);
}
```

新建了一个`NativeMessageQueue`：

```c++
NativeMessageQueue::NativeMessageQueue() :
        mPollEnv(NULL), mPollObj(NULL), mExceptionObj(NULL) {
    mLooper = Looper::getForThread();
    if (mLooper == NULL) {
        mLooper = new Looper(false);
        Looper::setForThread(mLooper);
    }
}
```

这里进行的初始化过程与`java`层的比较类似，都是新建了一个`Looper`对象存放入了`ThreadLocal`区域中。

当初始化过程完成之后，系统调用`Looper.loop()`开始消息循环：

```java
public static void loop() {
    final Looper me = myLooper();
    ...
    final MessageQueue queue = me.mQueue;
    ...
    for (;;) {
        Message msg = queue.next(); // might block
        if (msg == null) {
            // No message indicates that the message queue is quitting.
            return;
        }

        ...
        try {
            msg.target.dispatchMessage(msg);
        } finally {
            if (traceTag != 0) {
                Trace.traceEnd(traceTag);
            }
        }
        ...

        msg.recycleUnchecked();
    }
}
```

省略了大量代码，我们看到在这个无限循环中，首先就调用了`MessageQueue`的`next()`方法来获取下一条消息，注意这是一个阻塞调用，在下一条消息还没到时间或者没有下一条消息时候会被阻塞。

```java
Message next() {
    // Return here if the message loop has already quit and been disposed.
    // This can happen if the application tries to restart a looper after quit
    // which is not supported.
    final long ptr = mPtr;
    if (ptr == 0) {
        return null;
    }

    int pendingIdleHandlerCount = -1; // -1 only during first iteration
    int nextPollTimeoutMillis = 0;
    for (;;) {
        if (nextPollTimeoutMillis != 0) {
            Binder.flushPendingCommands();
        }

        nativePollOnce(ptr, nextPollTimeoutMillis);
        ...
    }
}
```

这里我们不关心`java`层后续对事件的处理，而是关心`java`层是如何调用`native`层的方法来对`native`消息队列中的事件进行处理的，因为我们的触摸事件是在`native`层进行处理再到`java`层进行分发的。

在`next()`方法中我们就调用了`nativePollOnce()`方法先去处理`native`中的事件：

```c++
static void android_os_MessageQueue_nativePollOnce(JNIEnv* env, jobject obj,
        jlong ptr, jint timeoutMillis) {
    NativeMessageQueue* nativeMessageQueue = reinterpret_cast<NativeMessageQueue*>(ptr);
    nativeMessageQueue->pollOnce(env, obj, timeoutMillis);
}
```

调用了`nativeMessageQueue`的`pollOnce()`方法：

```c++
void NativeMessageQueue::pollOnce(JNIEnv* env, jobject pollObj, int timeoutMillis) {
    mPollEnv = env;
    mPollObj = pollObj;
    mLooper->pollOnce(timeoutMillis);
    mPollObj = NULL;
    mPollEnv = NULL;

    if (mExceptionObj) {
        env->Throw(mExceptionObj);
        env->DeleteLocalRef(mExceptionObj);
        mExceptionObj = NULL;
    }
}
```

调用了`native` `Looper`的`pollOnce()`方法：

```c++
int Looper::pollOnce(int timeoutMillis, int* outFd, int* outEvents, void** outData) {
    int result = 0;
    for (;;) {
        ...
        result = pollInner(timeoutMillis);
    }
}
```

忽略特殊处理的过程，最终调用了`pollInner()`方法：（`PollInner()`的代码比较长，省略了大部分，标记了后面讨论的三个部分）

```c++
int Looper::pollInner(int timeoutMillis) {
	...// 省略初始化过程
    // Poll.
    int result = POLL_WAKE;
    mResponses.clear();
    mResponseIndex = 0;

    // We are about to idle.
    mPolling = true;
	/*-------1-------*/
    struct epoll_event eventItems[EPOLL_MAX_EVENTS];
    int eventCount = epoll_wait(mEpollFd, eventItems, EPOLL_MAX_EVENTS, timeoutMillis);
	
  	...
	/*---------------*/
	/*-------2-------*/
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
Done: ;
	...// 省略native message处理过程
      
    // Release lock.
    mLock.unlock();
	/*---------------*/
  	/*-------3-------*/
    // Invoke all response callbacks.
    for (size_t i = 0; i < mResponses.size(); i++) {
        Response& response = mResponses.editItemAt(i);
        if (response.request.ident == POLL_CALLBACK) {
            int fd = response.request.fd;
            int events = response.events;
            void* data = response.request.data;
#if DEBUG_POLL_AND_WAKE || DEBUG_CALLBACKS
            ALOGD("%p ~ pollOnce - invoking fd event callback %p: fd=%d, events=0x%x, data=%p",
                    this, response.request.callback.get(), fd, events, data);
#endif
            // Invoke the callback.  Note that the file descriptor may be closed by
            // the callback (and potentially even reused) before the function returns so
            // we need to be a little careful when removing the file descriptor afterwards.
            int callbackResult = response.request.callback->handleEvent(fd, events, data);
            if (callbackResult == 0) {
                removeFd(fd, response.request.seq);
            }

            // Clear the callback reference in the response structure promptly because we
            // will not clear the response vector itself until the next poll.
            response.request.callback.clear();
            result = POLL_CALLBACK;
        }
    }
  	/*---------------*/
    return result;
}
```

第一部分中，调用了`epoll_wait()`函数等待消息，当接收到消息或者发生超时的时候调用返回。

第二部分对返回的`events`进行遍历，如果对应的`fd`为唤醒专用的`mWakeEventFd`，执行`awoken()`函数清空管道，这个事件的作用只是为了唤醒`Looper`对新消息进行处理。

如果不是`mWakeEventFd`，说明为我们之前通过`addFd()`函数添加的`fd`，我们需要对这个`event`进行处理，处理函数为`pushResponse()`：

```c++
ssize_t requestIndex = mRequests.indexOfKey(fd);
pushResponse(events, mRequests.valueAt(requestIndex));
```

我们还记得在前面`addFd()`的过程中已经将`fd`作为索引，向`mRequest`中保存了`request`信息，信息中包含了`callback`也就是`NativeInputEventReceiver`对象。

```c++
void Looper::pushResponse(int events, const Request& request) {
    Response response;
    response.events = events;
    response.request = request;
    mResponses.push(response);
}
```

这里将`request`对象包装成了一个`response`，然后存入了`mResponses`中等待后面的处理。

第三部分中就是对于`response`的处理过程，主要就是这个调用：

```c++
int callbackResult = response.request.callback->handleEvent(fd, events, data);
```

调用了`callback`的`handleEvent()`，我们现在知道`callback`是前面保存的`NativeInputEventReceiver`对象。

现在，当原始事件通过建立好的`InputChannel`的`sendMessage()`函数发送触摸事件时：

```c++
status_t InputChannel::sendMessage(const InputMessage* msg) {
    size_t msgLength = msg->size();
    ssize_t nWrite;
    do {
        nWrite = ::send(mFd, msg, msgLength, MSG_DONTWAIT | MSG_NOSIGNAL);
    } while (nWrite == -1 && errno == EINTR);
	...
    return OK;
}

```

会直接调用`send()`函数向`fd`中写入数据，同时在另一边的`epoll_wait()`调用就会因`fd`数据的到来而唤醒，并通过`fd`找到注册好的`request`，进而调用`request`中的`NativeInputEventReceiver`的`handleEvent()`方法，参数就是我们接收到的事件信息与数据。

### handleEvent

```c++
int NativeInputEventReceiver::handleEvent(int receiveFd, int events, void* data) {
 	...
    if (events & ALOOPER_EVENT_INPUT) {
        JNIEnv* env = AndroidRuntime::getJNIEnv();
        status_t status = consumeEvents(env, false /*consumeBatches*/, -1, NULL);
        mMessageQueue->raiseAndClearException(env, "handleReceiveCallback");
        return status == OK || status == NO_MEMORY ? 1 : 0;
    }
	...
    return 1;
}
```

调用了`consumeEvents()`函数来处理事件，函数较长，我们拆开来看：

函数进行初始化过程之后执行了一个无限循环，循环体中的内容如下：

```c++
 InputEvent* inputEvent;
        status_t status = mInputConsumer.consume(&mInputEventFactory,
                consumeBatches, frameTime, &seq, &inputEvent);
```

首先就调用了`mInputConsumer`对象的`consume`方法接收并将原始的事件转换为分发过程中标准的`MotionEvent`：

```c++
status_t result = mChannel->receiveMessage(&mMsg);
```

这里就直接调用了`InputChannel`的`receiveMessage()`函数来接收另一端发送来的消息。

```c++
        switch (mMsg.header.type) {
        case InputMessage::TYPE_KEY: {
			...
        }

        case AINPUT_EVENT_TYPE_MOTION: {
			...
            MotionEvent* motionEvent = factory->createMotionEvent();
            if (! motionEvent) return NO_MEMORY;

            updateTouchState(&mMsg);
            initializeMotionEvent(motionEvent, &mMsg);
            *outSeq = mMsg.body.motion.seq;
            *outEvent = motionEvent;
#if DEBUG_TRANSPORT_ACTIONS
            ALOGD("channel '%s' consumer ~ consumed motion event, seq=%u",
                    mChannel->getName().string(), *outSeq);
#endif
            break;
        }
              
            }
```

这里对事件的类型进行了一个判断，当类型为`MOTION`即触摸事件时，新建了一个`MotionEvent`，然后用`mMsg`去进行初始化：

```c++
void InputConsumer::initializeMotionEvent(MotionEvent* event, const InputMessage* msg) {
    uint32_t pointerCount = msg->body.motion.pointerCount;
    PointerProperties pointerProperties[pointerCount];
    PointerCoords pointerCoords[pointerCount];
    for (uint32_t i = 0; i < pointerCount; i++) {
        pointerProperties[i].copyFrom(msg->body.motion.pointers[i].properties);
        pointerCoords[i].copyFrom(msg->body.motion.pointers[i].coords);
    }

    event->initialize(
            msg->body.motion.deviceId,
            msg->body.motion.source,
            msg->body.motion.action,
            msg->body.motion.actionButton,
            msg->body.motion.flags,
            msg->body.motion.edgeFlags,
            msg->body.motion.metaState,
            msg->body.motion.buttonState,
            msg->body.motion.xOffset,
            msg->body.motion.yOffset,
            msg->body.motion.xPrecision,
            msg->body.motion.yPrecision,
            msg->body.motion.downTime,
            msg->body.motion.eventTime,
            pointerCount,
            pointerProperties,
            pointerCoords);
}
```

然后在第14行把它存入了`outEvent`（也就是`consume()`函数中传入的`inputEvent`）中，现在函数返回到`NativeInputEventReceiver::consumeEvents()`继续处理：

```c++
  switch (inputEvent->getType()) {
            case AINPUT_EVENT_TYPE_KEY:
				...

            case AINPUT_EVENT_TYPE_MOTION: {
                if (kDebugDispatchCycle) {
                    ALOGD("channel '%s' ~ Received motion event.", getInputChannelName());
                }
                MotionEvent* motionEvent = static_cast<MotionEvent*>(inputEvent);
                if ((motionEvent->getAction() & AMOTION_EVENT_ACTION_MOVE) && outConsumedBatch) {
                    *outConsumedBatch = true;
                }
                inputEventObj = android_view_MotionEvent_obtainAsCopy(env, motionEvent);
                break;
            }
      		...
            }

            if (inputEventObj) {
                if (kDebugDispatchCycle) {
                    ALOGD("channel '%s' ~ Dispatching input event.", getInputChannelName());
                }
                env->CallVoidMethod(receiverObj.get(),
                        gInputEventReceiverClassInfo.dispatchInputEvent, seq, inputEventObj);
           ...
        }
```

下面就对`inputEvent`（即为`MotionEvent`）的类型作了一个判断，对`inputEventObj`（用于调用`java`层方法）进行赋值。随后就通过`JNI` 的`CallVoidMethod()`方法来调用`java`层的`dispatchInputEvent()`方法。这里调用的是`java`层`InputEventReceiver`的`dispatchInputEvent()`方法：

## 开始分发

### dispatchInputEvent

```java
private void dispatchInputEvent(int seq, InputEvent event) {
    mSeqMap.put(event.getSequenceNumber(), seq);
    onInputEvent(event);
}
```

`InputEventReceiver`是一个抽象类，具体实现类是`ViewRootImpl`的内部类`WindowInputEventReceiver`，它覆盖了`onInputEvent()`方法：

```java
@Override
public void onInputEvent(InputEvent event) {
    enqueueInputEvent(event, this, 0, true);
}
```

调用了`ViewRootImpl`的`enqueueInputEvent()`方法：

```java
void enqueueInputEvent(InputEvent event, InputEventReceiver receiver, int flags,
                       boolean processImmediately) {
    adjustInputEventForCompatibility(event);
    QueuedInputEvent q = obtainQueuedInputEvent(event, receiver, flags);

    // Always enqueue the input event in order, regardless of its time stamp.
    // We do this because the application or the IME may inject key events
    // in response to touch events and we want to ensure that the injected keys
    // are processed in the order they were received and we cannot trust that
    // the time stamp of injected events are monotonic.
    QueuedInputEvent last = mPendingInputEventTail;
    if (last == null) {
        mPendingInputEventHead = q;
        mPendingInputEventTail = q;
    } else {
        last.mNext = q;
        mPendingInputEventTail = q;
    }
    mPendingInputEventCount += 1;
    Trace.traceCounter(Trace.TRACE_TAG_INPUT, mPendingInputEventQueueLengthCounterName,
                       mPendingInputEventCount);

    if (processImmediately) {
        doProcessInputEvents();
    } else {
        scheduleProcessInputEvents();
    }
}
```

将接收到的事件加入了`mPendingInutEvent`链表的头部，注释里给出了这么做的原因：当发生事件插入的时候我们不能依赖事件的时间戳是准确的，因此必须让最新收到的事件先进行处理。

最终调用`doProcessInputEvents()`进行事件处理：

```java
void doProcessInputEvents() {
    // Deliver all pending input events in the queue.
    while (mPendingInputEventHead != null) {
        QueuedInputEvent q = mPendingInputEventHead;
        mPendingInputEventHead = q.mNext;
        if (mPendingInputEventHead == null) {
            mPendingInputEventTail = null;
        }
        q.mNext = null;

        mPendingInputEventCount -= 1;
        Trace.traceCounter(Trace.TRACE_TAG_INPUT, mPendingInputEventQueueLengthCounterName,
                mPendingInputEventCount);

        long eventTime = q.mEvent.getEventTimeNano();
        long oldestEventTime = eventTime;
        if (q.mEvent instanceof MotionEvent) {
            MotionEvent me = (MotionEvent)q.mEvent;
            if (me.getHistorySize() > 0) {
                oldestEventTime = me.getHistoricalEventTimeNano(0);
            }
        }
        mChoreographer.mFrameInfo.updateInputEventTime(eventTime, oldestEventTime);

        deliverInputEvent(q);
    }
	...
}
```

在从链表中取出事件之后，对事件的时间戳进行了更新。然后调用`deliverInputEvent()`方法：

```java
private void deliverInputEvent(QueuedInputEvent q) {
    Trace.asyncTraceBegin(Trace.TRACE_TAG_VIEW, "deliverInputEvent", q.mEvent.getSequenceNumber());
    if (mInputEventConsistencyVerifier != null) {
        mInputEventConsistencyVerifier.onInputEvent(q.mEvent, 0);
    }

    InputStage stage;
    if (q.shouldSendToSynthesizer()) {
        stage = mSyntheticInputStage;
    } else {
        stage = q.shouldSkipIme() ? mFirstPostImeInputStage : mFirstInputStage;
    }

    if (stage != null) {
        stage.deliver(q);
    } else {
        finishInputEvent(q);
    }
}
```

这段代码第一眼看上去比较难懂，`Stage`让我们联想到了CPU流水线处理过程中的`Stage`，这里就是进入了一个流水线过程来处理事件：

### 流水线事件处理

![](/images/event2_1.png)

![](/images/event2_2.png)

首先看到我们可以根据事件类型的需要从`mSyntheticInputStage` `EarlyPostImeInputStage` `NativePreImeInputStage`三个入口进入流水线，而流水线的每一步都对事件进行了不同的处理，并可以通过`forward()`方法传递到下一个`Stage`进行处理。并且这里使用的流水线是一个异步流水线，可以允许多个事件同时在里面运行处理，这种架构使得事件处理流程效率非常高。

那么我们的触摸事件从`NativePreImeInputStage`进入流水线后会经历什么处理过程呢：

我们并不是`IME`的事件，所以直接从`EarlyPostImeInputStage`开始：

#### EarlyPostImeInputStage

```java
@Override
protected int onProcess(QueuedInputEvent q) {
    if (q.mEvent instanceof KeyEvent) {
        return processKeyEvent(q);
    } else {
        final int source = q.mEvent.getSource();
        if ((source & InputDevice.SOURCE_CLASS_POINTER) != 0) {
            return processPointerEvent(q);
        }
    }
    return FORWARD;
}
```

第7行判断成立，进入`processPointerEvent()`：

```java
private int processPointerEvent(QueuedInputEvent q) {
    final MotionEvent event = (MotionEvent)q.mEvent;

    // Translate the pointer event for compatibility, if needed.
    if (mTranslator != null) {
        mTranslator.translateEventInScreenToAppWindow(event);
    }

    // Enter touch mode on down or scroll.
    final int action = event.getAction();
    if (action == MotionEvent.ACTION_DOWN || action == MotionEvent.ACTION_SCROLL) {
        ensureTouchMode(true);
    }

    // Offset the scroll position.
    if (mCurScrollY != 0) {
        event.offsetLocation(0, mCurScrollY);
    }

    // Remember the touch position for possible drag-initiation.
    if (event.isTouchEvent()) {
        mLastTouchPoint.x = event.getRawX();
        mLastTouchPoint.y = event.getRawY();
        mLastTouchSource = event.getSource();
    }
    return FORWARD;
}
```

对事件进行处理以后继续进入下一阶段。

#### NativePostImeInputStage

```java
@Override
protected int onProcess(QueuedInputEvent q) {
    if (mInputQueue != null) {
        mInputQueue.sendInputEvent(q.mEvent, q, false, this);
        return DEFER;
    }
    return FORWARD;
}
```

如果有事件等待被处理，则推迟当前事件的处理（实现异步）。否则直接进入下一个阶段：

#### ViewPostImeInputStage

```java
@Override
protected int onProcess(QueuedInputEvent q) {
    if (q.mEvent instanceof KeyEvent) {
        return processKeyEvent(q);
    } else {
        final int source = q.mEvent.getSource();
        if ((source & InputDevice.SOURCE_CLASS_POINTER) != 0) {
            return processPointerEvent(q);
        } else if ((source & InputDevice.SOURCE_CLASS_TRACKBALL) != 0) {
            return processTrackballEvent(q);
        } else {
            return processGenericMotionEvent(q);
        }
    }
}
```

第7行判断成立，调用`processPointerEvent()`方法：

```java
private int processPointerEvent(QueuedInputEvent q) {
    final MotionEvent event = (MotionEvent)q.mEvent;

    mAttachInfo.mUnbufferedDispatchRequested = false;
    final View eventTarget =
            (event.isFromSource(InputDevice.SOURCE_MOUSE) && mCapturingView != null) ?
                    mCapturingView : mView;
    mAttachInfo.mHandlingPointerEvent = true;
    boolean handled = eventTarget.dispatchPointerEvent(event);
	...
    return handled ? FINISH_HANDLED : FORWARD;
}
```

判断目标是否是`mCapturingView`，一般情况下目标就是`mView`（也就是当前`Window`的根`View`也就是`DecorView`），然后调用了它的`dispatchPointerEvent()`方法（继承自`View`）：

```java
public final boolean dispatchPointerEvent(MotionEvent event) {
    if (event.isTouchEvent()) {
        return dispatchTouchEvent(event);
    } else {
        return dispatchGenericMotionEvent(event);
    }
}
```

到这里，我们终于看到了熟悉的`dispatchTouchEvent()`方法，同时这也是一般事件分发机制分析的开始。

## 小结

现在，我们了解了从原始事件的产生地点到某个应用`UI`线程事件循环再到根`view`的`dispatchTouchEvent()`的整个流程。分析这个过程还是要再次感谢[Gityuan的博客](http://gityuan.com/)，这个过程找得到的资料只有他的文章，省了许多功夫。

下一篇文章开始就要讲解一般触摸事件分发分析的过程，也是参考资料比较多的部分。
