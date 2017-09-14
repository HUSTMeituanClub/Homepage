Title: Android 触摸事件分发机制（一）从内核到应用 一切的开始
Date: 2017-09-14 13:40:38
Category: Android
Tags: android, view
Authors: Di Wu

## 写在前面

**本文基于`Android 7.1.1 (API 25)`的源码分析编写**

安卓是基于触摸操作进行交互的系统，几乎所有的操作都由对屏幕的一次次触摸完成，如何正确处理触摸事件关乎整个应用的操作体验。因此安卓对于触摸事件的分发与处理机制也是我们学习安卓开发的重中之重。同时几乎每一个安卓技术博客中都会对触摸分发机制这一块进行详解，例如比较早期也是最为出名的[郭霖](http://blog.csdn.net/guolin_blog/article/details/9097463/)（《第一行代码》的作者）。现在网络上对于这一块的分析也已经比较详尽了，基本上一篇博客中遗漏的部分都可以在其他博客中找到答案。

但是无论别人的文章讲得多好，多么详细，我们都需要自己去打开源码仔细分析好好体会，一是这样一个比较复杂的过程不经历自己的思考很难完全理解，二是随着`api`版本的推进这部分源码也会发生很多变化，虽然大致思路相同，但是接触到新的内容总是一件好事。

这也就是我写这篇博文的原因：记录自己思考与分析的过程。

<!--more-->

## 触摸事件的来源

这部分的内容与安卓本身无关，代码大部分也都是`C++`实现的，中间的大部分内容来自于我对相关资料的总结，不在代码层面进行详细解释，只是说明一个流程，同时也会对代码进行大部分的删减，只关注最核心的那部分。

### 从硬件到内核

我们从头开始，从触摸事件最初最初的来源开始，我们知道内核是以处理中断的方式处理用户的输入的，触摸事件作为一种特殊的输入事件，自然也需要这种方式进行处理，只不过触摸事件的提供的信息要稍微复杂一些。

触摸事件来自于我们对硬件的操作，最初的来源当然是硬件引起的中断。而处理特定中断的代码则来自于对应硬件的驱动：

![](/images/event1_1.png)

[图片来源](http://newandroidbook.com/files/AndroidInput.pdf)（以下系列图片来源相同，不作标注）

当一个输入设备的驱动模块被首次载入内核的时候，会检测它应该管理的硬件设备，如果检测成功，驱动模块会调用`include/linux/input.h`中的`input_register_device(…)`函数设置一个`/dev/input/eventX`（`X`为整数）来代表这个输入设备。驱动模块同时也会通过`include/linux/interrupt.h`的`request_irq(…)`函数注册一个函数去处理这个硬件引发的中断，注册成功以后，当设备因用户交互而产生中断的时候就会交给对应的驱动模块进行处理。

驱动模块处理的细节各不相同，但最终都会将数据处理后存放进对应的`/dev/input/eventX`文件中。

![](/images/event1_2.png)

### 系统对触摸事件的处理

现在驱动程序为我们收集好了原始的输入信息并存放在了`eventX`文件中，下一步就是系统对于这个文件的处理并发送到应用层面。

![](/images/event1_3.png)

可以看到系统服务充当了从内核到应用的桥梁。

![](/images/event1_4.png)

系统服务由三个组件构成：`EventHub`、`InputReader`、`InputDispatcher`，关于它们的作用的详细分析在：

>   http://gityuan.com/2016/12/31/input-ipc/

下面对这个过程作简单介绍。

#### EventHub

文件在`frameworks/native/services/inputflinger/EventHub.cpp`

它的作用是监听、读取`/dev/input`目录下产生的新事件，并封装成`RawEvent`结构体供`InputReader`使用。

#### InputReader

文件在`frameworks/native/services/inputflinger/InputReader.cpp`

`InputReader`运行在一个单独的进程中，这个进程由`InputManagerService`的初始化而新建，具体内容请见：

>   http://gityuan.com/2016/12/10/input-manager/

它会在内部不断地循环调用`loopOnce()`方法来不断读取事件：

```cpp
void InputReader::loopOnce() {
    ...
    size_t count = mEventHub->getEvents(timeoutMillis, mEventBuffer, EVENT_BUFFER_SIZE);
    ...
    if (count) {
        processEventsLocked(mEventBuffer, count);
    }
    ...
}
```

第3行调用了`mEventHub`的`getEvent()`方法以获取事件。

第6行调用`processEventLocked()`方法来处理事件，经过一系列判断之后，会执行这行代码：

```cpp
device->process(rawEvents, count);
```

`process`函数会执行如下代码：

```cpp
InputMapper* mapper = mMappers[i];
mapper->process(rawEvent);
```

使用`mapper`去处理`rawEvent`，不同的输入事件类型会由不同的`mapper`去处理，以处理触摸事件的`TouchInputMapper`为例：

只看核心调用的话，会依次调用如下函数：

```cpp
void TouchInputMapper::process(const RawEvent* rawEvent)
void TouchInputMapper::sync(nsecs_t when)
void TouchInputMapper::processRawTouches(bool timeout)
void TouchInputMapper::cookAndDispatch(nsecs_t when)
void TouchInputMapper::dispatchTouches(nsecs_t when, uint32_t policyFlags) 
void TouchInputMapper::dispatchMotion(nsecs_t when, uint32_t policyFlags, uint32_t source,
        int32_t action, int32_t actionButton, int32_t flags,
        int32_t metaState, int32_t buttonState, int32_t edgeFlags,
        const PointerProperties* properties, const PointerCoords* coords,
        const uint32_t* idToIndex, BitSet32 idBits, int32_t changedId,
        float xPrecision, float yPrecision, nsecs_t downTime)
```

在最终的`dispatchMotion()`函数中执行以下代码：

```cpp
NotifyMotionArgs args(when, getDeviceId(), source, policyFlags,
        action, actionButton, flags, metaState, buttonState, edgeFlags,
        mViewport.displayId, pointerCount, pointerProperties, pointerCoords,
        xPrecision, yPrecision, downTime);
getListener()->notifyMotion(&args);
```

可以看到事件已经被处理成了一个`args`，然后调用`getListener()`：

```cpp
InputListenerInterface* InputReader::ContextImpl::getListener() {
    return mReader->mQueuedListener.get();
}
```

获取的是`mQueuedListener`，查看`notifyMotion()`函数：

```cpp
void QueuedInputListener::notifyMotion(const NotifyMotionArgs* args) {
    mArgsQueue.push(new NotifyMotionArgs(*args));
}
```

这里的`NotifyMotionArgs()`只是对事件进行了一次再封装。可以看到这个`args`最终进入了`QueuedInputListener`的`mArgsQueue`中。

我们再回到`InputReader`的`loopOnce()`函数中，函数在执行完上述调用到达最后一行时：

```cpp
mQueuedListener->flush();
```

调用`flush()`函数：

```cpp
void QueuedInputListener::flush() {
    size_t count = mArgsQueue.size();
    for (size_t i = 0; i < count; i++) {
        NotifyArgs* args = mArgsQueue[i];
        args->notify(mInnerListener);
        delete args;
    }
    mArgsQueue.clear();
}
```

调用了各`args`的`notify()`函数：

```cpp
void NotifyMotionArgs::notify(const sp<InputListenerInterface>& listener) const {
    listener->notifyMotion(this);
}
```

注意这里的`listener`传入的是`mInnerListener`，它是什么呢？

```cpp
QueuedInputListener::QueuedInputListener(const sp<InputListenerInterface>& innerListener) :
        mInnerListener(innerListener) {
}
```

在构造函数中初始化。

```cpp
InputReader::InputReader(const sp<EventHubInterface>& eventHub,
        const sp<InputReaderPolicyInterface>& policy,
        const sp<InputListenerInterface>& listener) :
        mContext(this), mEventHub(eventHub), mPolicy(policy),
        mGlobalMetaState(0), mGeneration(1),
        mDisableVirtualKeysTimeout(LLONG_MIN), mNextTimeout(LLONG_MAX),
        mConfigurationChangesToRefresh(0) {
    mQueuedListener = new QueuedInputListener(listener);

    { // acquire lock
        AutoMutex _l(mLock);

        refreshConfigurationLocked(0);
        updateGlobalMetaStateLocked();
    } // release lock
}
```

在`InputReader`构造函数中构造`QueuedInputListener`。

而`InputReader`是由`InputManager`类进行初始化的（线程的新建也在这个类中）：

```cpp
InputManager::InputManager(
        const sp<EventHubInterface>& eventHub,
        const sp<InputReaderPolicyInterface>& readerPolicy,
        const sp<InputDispatcherPolicyInterface>& dispatcherPolicy) {
    mDispatcher = new InputDispatcher(dispatcherPolicy);
    mReader = new InputReader(eventHub, readerPolicy, mDispatcher);
    initialize();
}
```

注意到第6行中，传入的`listener`正是`mDispatcher`也就是`InputDispatcher`对象。

所以说，`listener->notifyMotion(this);`调用的是`InputDispatcher`的`notifyMotion()`函数，至此，`InputReader`的工作已经完成，它从`EventHub`中循环读取地`rawEvent`事件，并处理成`args`再通知`InputDispatcher`对事件进行进一步的分发处理。

#### InputDispatcher

我们直接来到`InputDispatcher`的源码，路径：`frameworks/native/services/inputflinger/InputDispatcher.cpp`

上面说到最终调用了`InputDispatcher`的`notifyMotion`方法：

```c++
MotionEvent event;
event.initialize(args->deviceId, args->source, args->action, args->actionButton,args->flags, args->edgeFlags, args->metaState, args->buttonState, 0, 0, args->xPrecision, args->yPrecision, args->downTime, args->eventTime, args->pointerCount, args->pointerProperties, args->pointerCoords);
...
// Just enqueue a new motion event.
MotionEntry* newEntry = new MotionEntry(args->eventTime,
                args->deviceId, args->source, policyFlags,
                args->action, args->actionButton, args->flags,
                args->metaState, args->buttonState,
                args->edgeFlags, args->xPrecision, args->yPrecision, args->downTime,
                args->displayId,
                args->pointerCount, args->pointerProperties, args->pointerCoords, 0, 0);

needWake = enqueueInboundEventLocked(newEntry);
```

里面新建并初始化了一个`MotionEvent`，然后包装成一个`Entry`，然后调用`enqueueInboundEventLocked()`函数：

```c++
mInboundQueue.enqueueAtTail(entry);
```

在`enqueueInboundEventLocked()`函数中将这个`entry`插入到了`mInboundQueue`这个`InputDispatcher`维护的成员变量中。

到这里我们可以看到事件经过一系列的处理和传递以后最终作为一个`entry`插入到了`InputDispatcher`的队列中等待被进一步分发。

这个分发过程是在哪里进行的呢？

`InputDispatcher`线程的`threadLoop()`函数会被不断调用：

```c++
bool InputDispatcherThread::threadLoop() {
    mDispatcher->dispatchOnce();
    return true;
}
```

在`dispatcherOnce()`中：

```c++
if (!haveCommandsLocked()) {
	dispatchOnceInnerLocked(&nextWakeupTime);
}
```

在没有待执行的指令时执行`dispatchOnceInnerLocked()`函数：

```c++
mPendingEvent = mInboundQueue.dequeueAtHead();
```

这个函数中还包含了`ANR`的判断信息，关于`ANR`的部分之后再另开博客讲。

若`mInboundQueue`不为空，则从中取出头部的`pendingEvent`。

```c++
switch (mPendingEvent->type) {
case EventEntry::TYPE_CONFIGURATION_CHANGED: {
    ConfigurationChangedEntry *typedEntry = static_cast<ConfigurationChangedEntry *>(mPendingEvent);
    done = dispatchConfigurationChangedLocked(currentTime, typedEntry);
    dropReason = DROP_REASON_NOT_DROPPED; // configuration changes are never dropped
    break;
}

case EventEntry::TYPE_DEVICE_RESET: {
    DeviceResetEntry *typedEntry = static_cast<DeviceResetEntry *>(mPendingEvent);
    done = dispatchDeviceResetLocked(currentTime, typedEntry);
    dropReason = DROP_REASON_NOT_DROPPED; // device resets are never dropped
    break;
}

case EventEntry::TYPE_KEY: {
    KeyEntry *typedEntry = static_cast<KeyEntry *>(mPendingEvent);
    if (isAppSwitchDue) {
        if (isAppSwitchKeyEventLocked(typedEntry)) {
            resetPendingAppSwitchLocked(true);
            isAppSwitchDue = false;
        } else if (dropReason == DROP_REASON_NOT_DROPPED) {
            dropReason = DROP_REASON_APP_SWITCH;
        }
    }
    if (dropReason == DROP_REASON_NOT_DROPPED && isStaleEventLocked(currentTime, typedEntry)) {
        dropReason = DROP_REASON_STALE;
    }
    if (dropReason == DROP_REASON_NOT_DROPPED && mNextUnblockedEvent) {
        dropReason = DROP_REASON_BLOCKED;
    }
    done = dispatchKeyLocked(currentTime, typedEntry, &dropReason, nextWakeupTime);
    break;
}

case EventEntry::TYPE_MOTION: {
    MotionEntry *typedEntry = static_cast<MotionEntry *>(mPendingEvent);
    if (dropReason == DROP_REASON_NOT_DROPPED && isAppSwitchDue) {
        dropReason = DROP_REASON_APP_SWITCH;
    }
    if (dropReason == DROP_REASON_NOT_DROPPED && isStaleEventLocked(currentTime, typedEntry)) {
        dropReason = DROP_REASON_STALE;
    }
    if (dropReason == DROP_REASON_NOT_DROPPED && mNextUnblockedEvent) {
        dropReason = DROP_REASON_BLOCKED;
    }
    done = dispatchMotionLocked(currentTime, typedEntry, &dropReason, nextWakeupTime);
    break;
}

default:
    ALOG_ASSERT(false);
    break;
}
```

下面对取出的`mPendingEvent`的类型进行判断，根据不同的类型信息把它转换回原来的`Entry`信息，然后调用相应的分发方法，我们还是顺着触摸事件分发这条路继续向下走，调用了`bool InputDispatcher::dispatchMotionLocked()`函数：

```c++
int32_t injectionResult;
if (isPointerEvent) {
// Pointer event.  (eg. touchscreen)
	injectionResult = findTouchedWindowTargetsLocked(currentTime,
	entry, inputTargets, nextWakeupTime, &conflictingPointerActions);
} else {
// Non touch event.  (eg. trackball)
	injectionResult = findFocusedWindowTargetsLocked(currentTime,
                entry, inputTargets, nextWakeupTime);
}
```

对触摸或轨迹球事件做一个判断，再调用`findTouchedWindowTargesLocked()`函数：

```c++
int32_t pointerIndex = getMotionEventActionPointerIndex(action);
int32_t x = int32_t(entry->pointerCoords[pointerIndex].
                getAxisValue(AMOTION_EVENT_AXIS_X));
int32_t y = int32_t(entry->pointerCoords[pointerIndex].
                getAxisValue(AMOTION_EVENT_AXIS_Y));
```

在这里取出了`entry`里面的`pointerIndex`与触摸点坐标的`x` `y`值。

```c++
// 从前向后遍历所有的window以找出触摸的window
size_t numWindows = mWindowHandles.size();
for (size_t i = 0; i < numWindows; i++) {
    sp<InputWindowHandle> windowHandle = mWindowHandles.itemAt(i);
    const InputWindowInfo *windowInfo = windowHandle->getInfo();
    if (windowInfo->displayId != displayId) {
        continue; // 错误的window(displayId不匹配)
    }

    int32_t flags = windowInfo->layoutParamsFlags;
    if (windowInfo->visible) { // 如果window可见
        if (!(flags & InputWindowInfo::FLAG_NOT_TOUCHABLE)) {
            isTouchModal = (flags & (InputWindowInfo::FLAG_NOT_FOCUSABLE |
                                     InputWindowInfo::FLAG_NOT_TOUCH_MODAL)) == 0;
          // window可以被触摸
            if (isTouchModal || windowInfo->touchableRegionContainsPoint(x, y)) { // (x,y)在window内可触摸区域内
                newTouchedWindowHandle = windowHandle;
                break; // 找到触摸的window，保存在newTouchedWindowHandle中
            }
        }
		// 判断是否触摸window之外的区域
        if (maskedAction == AMOTION_EVENT_ACTION_DOWN &&
            (flags & InputWindowInfo::FLAG_WATCH_OUTSIDE_TOUCH)) {
            int32_t outsideTargetFlags = InputTarget::FLAG_DISPATCH_AS_OUTSIDE;
            if (isWindowObscuredAtPointLocked(windowHandle, x, y)) {
                outsideTargetFlags |= InputTarget::FLAG_WINDOW_IS_OBSCURED;
            } else if (isWindowObscuredLocked(windowHandle)) {
                outsideTargetFlags |= InputTarget::FLAG_WINDOW_IS_PARTIALLY_OBSCURED;
            }

            mTempTouchState.addOrUpdateWindow(windowHandle, outsideTargetFlags, BitSet32(0));
        }
    }
}
```

这段代码的目的是为了遍历所有的`window`找到触摸对应的那个`window`。

```c++
// Handle the case where we did not find a window.
if (newTouchedWindowHandle == NULL) {
    // Try to assign the pointer to the first foreground window we find, if there is one.
    newTouchedWindowHandle = mTempTouchState.getFirstForegroundWindowHandle();
    if (newTouchedWindowHandle == NULL) {
        ALOGI("Dropping event because there is no touchable window at (%d, %d).", x, y);
        injectionResult = INPUT_EVENT_INJECTION_FAILED;
        goto Failed;
    }
}
```

如果遍历后没有找到合适的`window`，那就取第一个前台的`window`。

然后通过`addWindowTargetLocked()`方法把缓存下来的结果存放入`inputTargets`中。

```c++
for (size_t i = 0; i < mTempTouchState.windows.size(); i++) {
	const TouchedWindow& touchedWindow = mTempTouchState.windows.itemAt(i);
	addWindowTargetLocked(touchedWindow.windowHandle, touchedWindow.targetFlags,
	touchedWindow.pointerIds, inputTargets);
}
```

```c++
void InputDispatcher::addWindowTargetLocked(const sp<InputWindowHandle>& windowHandle,
        int32_t targetFlags, BitSet32 pointerIds, Vector<InputTarget>& inputTargets) {
    inputTargets.push();

    const InputWindowInfo* windowInfo = windowHandle->getInfo();
    InputTarget& target = inputTargets.editTop();
    target.inputChannel = windowInfo->inputChannel;
    target.flags = targetFlags;
    target.xOffset = - windowInfo->frameLeft;
    target.yOffset = - windowInfo->frameTop;
    target.scaleFactor = windowInfo->scaleFactor;
    target.pointerIds = pointerIds;
}
```

函数将原始的`window`数据进行了再次封装。

找到合适的`window`或是没有找到（处理错误）之后，函数返回到`bool InputDispatcher::dispatchMotionLocked()`中：

```c++
dispatchEventLocked(currentTime, entry, inputTargets);
```

开始向`inputTargets`中的目录分发事件：

```c++
void InputDispatcher::dispatchEventLocked(nsecs_t currentTime,
        EventEntry* eventEntry, const Vector<InputTarget>& inputTargets) {
...
    for (size_t i = 0; i < inputTargets.size(); i++) {
        const InputTarget& inputTarget = inputTargets.itemAt(i); // 遍历目标

        ssize_t connectionIndex = getConnectionIndexLocked(inputTarget.inputChannel); // 见下文
        if (connectionIndex >= 0) {
            sp<Connection> connection = mConnectionsByFd.valueAt(connectionIndex);
            prepareDispatchCycleLocked(currentTime, connection, eventEntry, &inputTarget);
        } else {
...
        }
    }
}
```

`inputTarget`中包含的`inputChannel`就是后面用于与`window`实例通信的关键：

```c++
/*
 * An input channel consists of a local unix domain socket used to send and receive
 * input messages across processes.  Each channel has a descriptive name for debugging purposes.
 *
 * Each endpoint has its own InputChannel object that specifies its file descriptor.
 *
 * The input channel is closed when all references to it are released.
 */
class InputChannel : public RefBase {
  protected:
    virtual ~InputChannel();

public:
    InputChannel(const String8& name, int fd);

    /* Creates a pair of input channels.
     *
     * Returns OK on success.
     */
    static status_t openInputChannelPair(const String8& name,
            sp<InputChannel>& outServerChannel, sp<InputChannel>& outClientChannel);

    inline String8 getName() const { return mName; }
    inline int getFd() const { return mFd; }

    /* Sends a message to the other endpoint.
     *
     * If the channel is full then the message is guaranteed not to have been sent at all.
     * Try again after the consumer has sent a finished signal indicating that it has
     * consumed some of the pending messages from the channel.
     *
     * Returns OK on success.
     * Returns WOULD_BLOCK if the channel is full.
     * Returns DEAD_OBJECT if the channel's peer has been closed.
     * Other errors probably indicate that the channel is broken.
     */
    status_t sendMessage(const InputMessage* msg);

    /* Receives a message sent by the other endpoint.
     *
     * If there is no message present, try again after poll() indicates that the fd
     * is readable.
     *
     * Returns OK on success.
     * Returns WOULD_BLOCK if there is no message present.
     * Returns DEAD_OBJECT if the channel's peer has been closed.
     * Other errors probably indicate that the channel is broken.
     */
    status_t receiveMessage(InputMessage* msg);

    /* Returns a new object that has a duplicate of this channel's fd. */
    sp<InputChannel> dup() const;

private:
    String8 mName;
    int mFd;
};
```

>   `InputChannel`包含了一个本地`unix socket`用于跨进程发送与接收输入信息。

它的接口十分简单，我们就通过`sendMessage()`与`receiveMessage()`两个函数实现跨进程通信。

回到之前，我们通过这个`inputChannel`的`Fd`来获取一个`Connection`的索引，然后根据这个索引从`mConnectionsByFd`中获取`connection`对象。

```c++
ssize_t InputDispatcher::getConnectionIndexLocked(const sp<InputChannel>& inputChannel) {
    ssize_t connectionIndex = mConnectionsByFd.indexOfKey(inputChannel->getFd());
    if (connectionIndex >= 0) {
        sp<Connection> connection = mConnectionsByFd.valueAt(connectionIndex);
        if (connection->inputChannel.get() == inputChannel.get()) {
            return connectionIndex;
        }
    }
    return -1;
}
```

这个`mConnectionByFd`又是怎么建立起来的呢？在`InputDispatcher`中包含了一个`registerInputChannel`函数：

```c++
status_t InputDispatcher::registerInputChannel(const sp<InputChannel>& inputChannel,
        const sp<InputWindowHandle>& inputWindowHandle, bool monitor) {
...
    { // acquire lock
        AutoMutex _l(mLock);

...
        sp<Connection> connection = new Connection(inputChannel, inputWindowHandle, monitor);

        int fd = inputChannel->getFd();
        mConnectionsByFd.add(fd, connection);

        if (monitor) {
            mMonitoringChannels.push(inputChannel);
        }

        mLooper->addFd(fd, 0, ALOOPER_EVENT_INPUT, handleReceiveCallback, this); 
    } // release lock

    // Wake the looper because some connections have changed.
    mLooper->wake();
    return OK;
}
```

`connection`对象就是在这里由`inputChannel`构造并加入到`mConnectionsByFd`中的。而`mConnectionsByFd`本身是一个以`Fd`为索引的键值对：

```c++
KeyedVector<int, sp<Connection> > mConnectionsByFd;
```

取得`connection`对象之后，进入到了`prepareDispatchCycleLocked()`函数中，这个函数对连接的状态是否正常进行检测，连接正常会调用`enqueueDispatchEntriesLocked()`函数：

```c++
void InputDispatcher::enqueueDispatchEntriesLocked(nsecs_t currentTime,
        const sp<Connection>& connection, EventEntry* eventEntry, const InputTarget* inputTarget) {
    bool wasEmpty = connection->outboundQueue.isEmpty();

    // Enqueue dispatch entries for the requested modes.
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_HOVER_EXIT);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_OUTSIDE);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_HOVER_ENTER);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_IS);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_SLIPPERY_EXIT);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_SLIPPERY_ENTER);

    // If the outbound queue was previously empty, start the dispatch cycle going.
    if (wasEmpty && !connection->outboundQueue.isEmpty()) {
        startDispatchCycleLocked(currentTime, connection);
    }
}
```

中间调用了一系列的`enqueueDispatchEntryLocked()`函数：

```c++
void InputDispatcher::enqueueDispatchEntryLocked(
        const sp<Connection>& connection, EventEntry* eventEntry, const InputTarget* inputTarget,
        int32_t dispatchMode) {
    int32_t inputTargetFlags = inputTarget->flags;
    if (!(inputTargetFlags & dispatchMode)) {
        return;
    }
    inputTargetFlags = (inputTargetFlags & ~InputTarget::FLAG_DISPATCH_MASK) | dispatchMode;

    // This is a new event.
    // Enqueue a new dispatch entry onto the outbound queue for this connection.
    DispatchEntry* dispatchEntry = new DispatchEntry(eventEntry, // increments ref
            inputTargetFlags, inputTarget->xOffset, inputTarget->yOffset,
            inputTarget->scaleFactor);
...
    // Enqueue the dispatch entry.
    connection->outboundQueue.enqueueAtTail(dispatchEntry);
    traceOutboundQueueLengthLocked(connection);
...
}
```

省略的代码对`entry`进行了进一步的包装，然后在最后加入到了`connection`维护的`outboundQueue`中。

回到上面，之后调用`startDispatchCycleLocked()`正式开始分发事件：

```c++
  while (connection->status == Connection::STATUS_NORMAL
            && !connection->outboundQueue.isEmpty()) {
        DispatchEntry* dispatchEntry = connection->outboundQueue.head;
        dispatchEntry->deliveryTime = currentTime;

        // Publish the event.
        status_t status;
        EventEntry* eventEntry = dispatchEntry->eventEntry;
        switch (eventEntry->type) {
```

从`connection`的`outboundQueue`取出`entry`之后，根据事件类型的不同对事件进一步处理：

```c++
 case EventEntry::TYPE_MOTION: {
            MotionEntry* motionEntry = static_cast<MotionEntry*>(eventEntry);

            PointerCoords scaledCoords[MAX_POINTERS];
            const PointerCoords* usingCoords = motionEntry->pointerCoords;

            // Set the X and Y offset depending on the input source.
            float xOffset, yOffset, scaleFactor;
            if ((motionEntry->source & AINPUT_SOURCE_CLASS_POINTER)
                    && !(dispatchEntry->targetFlags & InputTarget::FLAG_ZERO_COORDS)) {
                scaleFactor = dispatchEntry->scaleFactor;
                xOffset = dispatchEntry->xOffset * scaleFactor;
                yOffset = dispatchEntry->yOffset * scaleFactor;
                if (scaleFactor != 1.0f) {
                    for (uint32_t i = 0; i < motionEntry->pointerCount; i++) {
                        scaledCoords[i] = motionEntry->pointerCoords[i];
                        scaledCoords[i].scale(scaleFactor);
                    }
                    usingCoords = scaledCoords;
                }
            } else {
                xOffset = 0.0f;
                yOffset = 0.0f;
                scaleFactor = 1.0f;

                // We don't want the dispatch target to know.
                if (dispatchEntry->targetFlags & InputTarget::FLAG_ZERO_COORDS) {
                    for (uint32_t i = 0; i < motionEntry->pointerCount; i++) {
                        scaledCoords[i].clear();
                    }
                    usingCoords = scaledCoords;
                }
            }



```

在对事件的坐标进行解析（缩放）之后，进入下面的发布过程：

```c++
            // Publish the motion event.
            status = connection->inputPublisher.publishMotionEvent(dispatchEntry->seq,
                    motionEntry->deviceId, motionEntry->source,
                    dispatchEntry->resolvedAction, motionEntry->actionButton,
                    dispatchEntry->resolvedFlags, motionEntry->edgeFlags,
                    motionEntry->metaState, motionEntry->buttonState,
                    xOffset, yOffset, motionEntry->xPrecision, motionEntry->yPrecision,
                    motionEntry->downTime, motionEntry->eventTime,
                    motionEntry->pointerCount, motionEntry->pointerProperties,
                    usingCoords);
            break;
        }
```

实际上调用了`InputPublisher`的`publishMotionEvent()`函数：

```c++
    InputMessage msg;
    msg.header.type = InputMessage::TYPE_MOTION;
    msg.body.motion.seq = seq;
    msg.body.motion.deviceId = deviceId;
    msg.body.motion.source = source;
    msg.body.motion.action = action;
    msg.body.motion.actionButton = actionButton;
    msg.body.motion.flags = flags;
    msg.body.motion.edgeFlags = edgeFlags;
    msg.body.motion.metaState = metaState;
    msg.body.motion.buttonState = buttonState;
    msg.body.motion.xOffset = xOffset;
    msg.body.motion.yOffset = yOffset;
    msg.body.motion.xPrecision = xPrecision;
    msg.body.motion.yPrecision = yPrecision;
    msg.body.motion.downTime = downTime;
    msg.body.motion.eventTime = eventTime;
    msg.body.motion.pointerCount = pointerCount;
    for (uint32_t i = 0; i < pointerCount; i++) {
        msg.body.motion.pointers[i].properties.copyFrom(pointerProperties[i]);
        msg.body.motion.pointers[i].coords.copyFrom(pointerCoords[i]);
    }
    return mChannel->sendMessage(&msg);
```

函数里封装了一个`msg`，然后最终调用了`mChannel`的`sendMessage()`方法进行跨进程通信。

---

现在我们到了图中的这一步：

![](/images/event1_5.png)

我们的点击事件来到了建立的`socket`中，准备与交付给对应的`app`，我们知道每个`app`运行在自己的进程中，所以就需要使用`socket`来进行跨进程通信。

---

### InputChannel连接建立过程

本段内容主要参考了

>   http://gityuan.com/2016/12/24/input-ui/

详细分析及代码请移步上面链接。

连接的建立是在一个`Activity`启动时进行的。

`Activity`的启动是一个比较复杂的过程，会经过`ActivityManagerService`与`WindowManagerService`的层层调用，最终到达`WindowManagerGlobal`的`addView()`方法。 

```java
    public void addView(View view, ViewGroup.LayoutParams params,
            Display display, Window parentWindow) {
        ...
        ViewRootImpl root;
        View panelParentView = null;
        ...

        root = new ViewRootImpl(view.getContext(), display);
        ... 

        root.setView(view, wparams, panelParentView);
        ...
    }
```

在`addView`中，创建并初始化了一个`ViewRootImpl`对象，并调用了它的`setView()`方法。

`ViewRootImpl`的初始化过程：

```java
    public ViewRootImpl(Context context, Display display) {
        ...
        mWindowSession = WindowManagerGlobal.getWindowSession();
        ...
    }
```

这里我们关注的是这个`mWindowSession`对象的初始化。

```java
    public static IWindowSession getWindowSession() {
        synchronized (WindowManagerGlobal.class) {
            if (sWindowSession == null) {
                try {
                    InputMethodManager imm = InputMethodManager.getInstance(); 
                    IWindowManager windowManager = getWindowManagerService();
                    // 获取Session对象，利用Binder机制调用系统线程的方法
                    sWindowSession = windowManager.openSession(
                            new IWindowSessionCallback.Stub() {
                                @Override
                                public void onAnimatorScaleChanged(float scale) {
                                    ValueAnimator.setDurationScale(scale);
                                }
                            },
                            imm.getClient(), imm.getInputContext());
                } catch (RemoteException e) {
                    throw e.rethrowFromSystemServer();
                }
            }
            return sWindowSession;
        }
    }
```

下面是`setView()`：

```java
    public void setView(View view, WindowManager.LayoutParams attrs, View panelParentView) {
        ...
        // 服务端过程
        res = mWindowSession.addToDisplay(mWindow, mSeq, mWindowAttributes,
            getHostVisibility(), mDisplay.getDisplayId(),
            mAttachInfo.mContentInsets, mAttachInfo.mStableInsets,
            mAttachInfo.mOutsets, mInputChannel);
        ...
        // 客户端过程
        if (mInputChannel != null) {
            mInputEventReceiver = new WindowInputEventReceiver(mInputChannel, Looper.myLooper());
        }
        ...
    }
```

上面的两行语句分别的对应两个注册过程的开始，先执行服务端的注册与监听，再执行客户端的注册与监听。

下面对这两个过程分别进行追踪。

#### 服务端过程

通过刚刚获取的`mWindowSession`去调用系统线程中的`addToDisplay()`方法：

```java
    @Override
    public int addToDisplay(IWindow window, int seq, WindowManager.LayoutParams attrs,
            int viewVisibility, int displayId, Rect outContentInsets, Rect outStableInsets,
            Rect outOutsets, InputChannel outInputChannel) {
        return mService.addWindow(this, window, seq, attrs, viewVisibility, displayId,
                outContentInsets, outStableInsets, outOutsets, outInputChannel);
    }
...

这个`mService`自然就是之前获取它使用的`WindowManagerService`，调用它的`addWindow()`方法：

​```java
    public int addWindow(Session session, IWindow client, int seq,
            WindowManager.LayoutParams attrs, int viewVisibility, int displayId,
            Rect outContentInsets, Rect outStableInsets, Rect outOutsets,
            InputChannel outInputChannel) {
                ...
                WindowState win = new WindowState(this, session, client, token,
                    attachedWindow, appOp[0], seq, attrs, viewVisibility, displayContent);
                ...
                final boolean openInputChannels = (outInputChannel != null
                    && (attrs.inputFeatures & INPUT_FEATURE_NO_INPUT_CHANNEL) == 0);
                if  (openInputChannels) {
                    win.openInputChannel(outInputChannel);
                }
            ...
            }
```

我们关注的是它创建并初始化了`WindowState`对象，然后调用了它的`openInputChannel()`方法：

```java
    void openInputChannel(InputChannel outInputChannel) {
        if (mInputChannel != null) {
            throw new IllegalStateException("Window already has an input channel.");
        }
        String name = makeInputChannelName();
        InputChannel[] inputChannels = InputChannel.openInputChannelPair(name);
        mInputChannel = inputChannels[0]; // 这里将服务端的inputChannel保存在了WindowState中
        mClientChannel = inputChannels[1];
        mInputWindowHandle.inputChannel = inputChannels[0];
        if (outInputChannel != null) {
            mClientChannel.transferTo(outInputChannel);
            mClientChannel.dispose();
            mClientChannel = null;
        } else {
            // If the window died visible, we setup a dummy input channel, so that taps
            // can still detected by input monitor channel, and we can relaunch the app.
            // Create dummy event receiver that simply reports all events as handled.
            mDeadWindowEventReceiver = new DeadWindowEventReceiver(mClientChannel);
        }
        mService.mInputManager.registerInputChannel(mInputChannel, mInputWindowHandle);
    }
```

在这里创建了两个`InputChannel`对象，其中作为服务端存放在系统进程中的是`inputChannels[0]`，作为客户端的存放在`app`的`ui`主线程中的是`inputChannels[1]`。它们的传递过程之后再看，我们先看`InputChannel`建立时调用的`openInputChannelPair()`方法：

```java
    public static InputChannel[] openInputChannelPair(String name) {
        if (name == null) {
            throw new IllegalArgumentException("name must not be null");
        }

        if (DEBUG) {
            Slog.d(TAG, "Opening input channel pair '" + name + "'");
        }
        return nativeOpenInputChannelPair(name);
    }
```

调用了`native`方法：

```c++
static jobjectArray android_view_InputChannel_nativeOpenInputChannelPair(JNIEnv* env,
        jclass clazz, jstring nameObj) {
    ...
    sp<InputChannel> serverChannel;
    sp<InputChannel> clientChannel;
    status_t result = InputChannel::openInputChannelPair(name, serverChannel, clientChannel);
    ...
    return channelPair;
}
```

```c++
status_t InputChannel::openInputChannelPair(const String8& name,
        sp<InputChannel>& outServerChannel, sp<InputChannel>& outClientChannel) {
    int sockets[2];
    if (socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sockets)) {
        status_t result = -errno;
        ALOGE("channel '%s' ~ Could not create socket pair.  errno=%d",
                name.string(), errno);
        outServerChannel.clear();
        outClientChannel.clear();
        return result;
    }

    int bufferSize = SOCKET_BUFFER_SIZE;
    setsockopt(sockets[0], SOL_SOCKET, SO_SNDBUF, &bufferSize, sizeof(bufferSize));
    setsockopt(sockets[0], SOL_SOCKET, SO_RCVBUF, &bufferSize, sizeof(bufferSize));
    setsockopt(sockets[1], SOL_SOCKET, SO_SNDBUF, &bufferSize, sizeof(bufferSize));
    setsockopt(sockets[1], SOL_SOCKET, SO_RCVBUF, &bufferSize, sizeof(bufferSize));

    String8 serverChannelName = name;
    serverChannelName.append(" (server)");
    outServerChannel = new InputChannel(serverChannelName, sockets[0]);

    String8 clientChannelName = name;
    clientChannelName.append(" (client)");
    outClientChannel = new InputChannel(clientChannelName, sockets[1]);
    return OK;
}
```

就是在这里真正创建了`InputChannel`所使用的`socket`实体。

现在我们回到`WindowState`的`openInputChannel()`方法中，在成功创建两个`InputChannel`后，调用了`        mService.mInputManager.registerInputChannel(mInputChannel, mInputWindowHandle);`：

```java
    public void registerInputChannel(InputChannel inputChannel,
            InputWindowHandle inputWindowHandle) {
        if (inputChannel == null) {
            throw new IllegalArgumentException("inputChannel must not be null.");
        }

        nativeRegisterInputChannel(mPtr, inputChannel, inputWindowHandle, false);
    }
```

```c++
static void nativeRegisterInputChannel(JNIEnv* env, jclass /* clazz */,
        jlong ptr, jobject inputChannelObj, jobject inputWindowHandleObj, jboolean monitor) {
    NativeInputManager* im = reinterpret_cast<NativeInputManager*>(ptr);

    sp<InputChannel> inputChannel = android_view_InputChannel_getInputChannel(env,
            inputChannelObj);
    ...
    sp<InputWindowHandle> inputWindowHandle =
            android_server_InputWindowHandle_getHandle(env, inputWindowHandleObj);

    status_t status = im->registerInputChannel(
            env, inputChannel, inputWindowHandle, monitor);
    ...
}
```

```c++
status_t NativeInputManager::registerInputChannel(JNIEnv* /* env */,
        const sp<InputChannel>& inputChannel,
        const sp<InputWindowHandle>& inputWindowHandle, bool monitor) {
    return mInputManager->getDispatcher()->registerInputChannel(
            inputChannel, inputWindowHandle, monitor);
}
```

`getDispatcher()`返回了`InputDispatcher`对象，这个方法就调用了我们之前提到过的`InputDispatcher::registerInputchannel()`方法，向`InputDispatcher`注册了我们创建好的`InputChannel`服务端。

我们回顾一下这个方法：

```c++
status_t InputDispatcher::registerInputChannel(const sp<InputChannel>& inputChannel,
        const sp<InputWindowHandle>& inputWindowHandle, bool monitor) {
...
    { // acquire lock
        AutoMutex _l(mLock);

...
        sp<Connection> connection = new Connection(inputChannel, inputWindowHandle, monitor);

        int fd = inputChannel->getFd();
        mConnectionsByFd.add(fd, connection);

        if (monitor) {
            mMonitoringChannels.push(inputChannel);
        }

        mLooper->addFd(fd, 0, ALOOPER_EVENT_INPUT, handleReceiveCallback, this); 
    } // release lock

    // Wake the looper because some connections have changed.
    mLooper->wake();
    return OK;
}
```

在将`InputChannel`的`Fd`作为索引保存到`InputDispatcher`中时，同时传入了`handleReceiveCallback()`函数作为参数，在服务端收到消息时进行回调。

#### 客户端过程

```java
        // 客户端过程
        if (mInputChannel != null) {
            mInputEventReceiver = new WindowInputEventReceiver(mInputChannel, Looper.myLooper());
        }
```

这里以客户端`InputChannel`与当前应用的`Looper`作为参数，初始化了`WindowInputEventReceiver`对象：

```java
    public InputEventReceiver(InputChannel inputChannel, Looper looper) {
        ...
        mInputChannel = inputChannel;
        mMessageQueue = looper.getQueue();
        mReceiverPtr = nativeInit(new WeakReference<InputEventReceiver>(this),
                inputChannel, mMessageQueue);

        mCloseGuard.open("dispose");
    }
```

获取了`app`进程的消息队列，并调用`native`方法对`mReceiverPtr`进行初始化：

```c++
static jlong nativeInit(JNIEnv* env, jclass clazz, jobject receiverWeak,
        jobject inputChannelObj, jobject messageQueueObj) {
    ...
    sp<InputChannel> inputChannel = android_view_InputChannel_getInputChannel(env,
            inputChannelObj); 

    sp<MessageQueue> messageQueue = android_os_MessageQueue_getMessageQueue(env, messageQueueObj);
    ...

    sp<NativeInputEventReceiver> receiver = new NativeInputEventReceiver(env,
            receiverWeak, inputChannel, messageQueue);
    status_t status = receiver->initialize();
    ...
    receiver->incStrong(gInputEventReceiverClassInfo.clazz); // retain a reference for the object
    return reinterpret_cast<jlong>(receiver.get());
}
```

创建了`NativeInputEventReceiver`对象，并调用`initialize()`方法进行初始化：

```c++
status_t NativeInputEventReceiver::initialize() {
    setFdEvents(ALOOPER_EVENT_INPUT);
    return OK;
}
```

```c++
void NativeInputEventReceiver::setFdEvents(int events) {
    if (mFdEvents != events) {
        mFdEvents = events;
        int fd = mInputConsumer.getChannel()->getFd();
        if (events) {
            mMessageQueue->getLooper()->addFd(fd, 0, events, this, NULL);
        } else {
            mMessageQueue->getLooper()->removeFd(fd);
        }
    }
}
```

这里将客户端的`InputChannel`的`Fd`加入到了`Looper`中作为监听信号，对返回的消息进行监听处理：

```c++
int Looper::addFd(int fd, int ident, int events, const sp<LooperCallback>& callback, void* data) {
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
                    ...
                ...
                }
            ...
        }
       
       }
}
```

这里将`NativeInputEventReceiver`传入的`this`作为`callback`存入到`request`中， 再以`fd`为索引向`mRequests`映射表中加入`request`，然后以`fd`作为信号调用`epoll_ctl`系统调用，利用它对通信过程进行监听，在收到消息之后最终会根据`fd`找到`mRequests`中的`request`保存的`callback`，即`NativeInputEventReceiver`对象。

![](/images/event1_6.png)

### 小结

现在我们了解了从内核到应用整个触摸事件的传输过程，并且知道了`InputChannel`在两端的监听建立与触发的函数，至此，触摸事件已经从系统底层来到了我们的应用进程，下一篇博客将从触发函数开始讲解事件从`native`层真正传入`java`层的过程。
