Title:  Android Context理解与陷阱
Date: 2017-07-19 19:07:42
Category: Android
Tags: android
Authors: Di Wu


## Context?

`Context`在安卓开发时是一个非常常见的组件，我们会在许多地方使用它，举一些例子：

*   启动新的`Activity` `Service`
*   发送广播，接收广播
*   填充`View`
*   获取资源

相信每一个开发者在看见它时都有过这样一些疑问：

*   `Context`是什么
*   `Context`的作用
*   `Context`从哪里来

同时，我们也经历过需要一个`Context`但不知道如何去正确获取/传递的情况，事实上不正确地保存一个`Context`的引用可能会导致部分内存不能被正确GC从而造成事实上的内存泄漏。

本文将着重对上面这些内容进行讲解。

<!--more-->

## Context的定义

字面上解释，`Context`意为“环境”，这个解释比较符合它的作用。

官方文档中对`Context`的解释是：

>   Interface to global information about an application environment. This is an abstract class whose implementation is provided by the Android system. It allows access to application-specific resources and classes, as well as up-calls for application-level operations such as launching activities, broadcasting and receiving intents, etc.
>
>   关于应用环境的全局信息的接口。它是一个抽象类，具体由安卓系统来实现。它允许我们去访问特定的应用的资源和类，同时也可以经由它去向上请求应用级别的操作例如启动`Activity`、发送广播、接收`intents`等等。

我们可以把它看作是一个连接我们代码与安卓系统的“桥梁”，我们开发的应用是与运行在设备上的操作系统紧密相关的，只能通过操作系统，我们才能去启动一个新的`Activity`，向其他应用发送广播，启动一个新的`Service`或是访问我们存放在`apk`中的资源文件。

`Context`就是系统为我们提供上述功能的一个接口，我们需要使用它去完成与系统的信息交换。

## Context从哪里来

`Context`作为一个依赖于系统的类，`SDK`中只给了我们一个抽象类，具体的实现由系统完成，下文举例使用的`ContextImpl`就是`AOSP`中安卓源码对于`Context`的一个实现。

## Context的作用

### Context中封装的信息

我们可以看看`Context`里面包含了哪些东西（部分）。

```java
private final String mBasePackageName; 
private final String mOpPackageName; //软件包名
private final Resources mResources;
private final ResourcesManager mResourcesManager; //用于管理资源文件
private final Display mDisplay; //为View填充等提供屏幕尺寸、像素密度等信息
private final DisplayAdjustments mDisplayAdjustments = new DisplayAdjustments();
private Resources.Theme mTheme = null; //主题信息
private File mCacheDir;
@GuardedBy("mSync")
private File mCodeCacheDir;
...
@GuardedBy("mSync")
private File[] mExternalObbDirs;
@GuardedBy("mSync")
private File[] mExternalFilesDirs;
@GuardedBy("mSync")
private File[] mExternalCacheDirs;
@GuardedBy("mSync")
private File[] mExternalMediaDirs; //各种文件路径
```

这些域的存在为功能提供了必要的信息，例如在`LayoutInflater`填充`View`时需要一个`context`作为参数，我们查看这个`context`如何被使用：

```java
final XmlResourceParser childParser = context.getResources().getLayout(layout);
```

我们传入的`ResourceId`最终会被通过`context`的`getResource()`方法获取的`Resource`对象的`getLayout()`方法定位到对应的`xml`文件提供给`Inflater`进行解析。

```java
// Apply a theme wrapper, if allowed and one is specified.
if (!ignoreThemeAttr) {
    final TypedArray ta = context.obtainStyledAttributes(attrs, ATTRS_THEME);
    final int themeResId = ta.getResourceId(0, 0);
    if (themeResId != 0) {
        context = new ContextThemeWrapper(context, themeResId);
    }
    ta.recycle();
}
```

在这里调用了`context`的`obtainStyledAttributes()`方法：

```java
public final TypedArray obtainStyledAttributes(
        AttributeSet set, @StyleableRes int[] attrs) {
    return getTheme().obtainStyledAttributes(set, attrs, 0, 0);
}
```

最终使用了`context`中存放的主题信息为填充的`view`设置属性。

现在我们知道，我们存放在`res`文件夹下的内容（布局文件、字符串文件、图片、主题……）都需要通过一个`context`去向系统获取。

那么为什么在启动`activity`、启动`service`、发送广播时都需要使用`context`呢？因为这些操作与系统是紧密相关的，我们知道启动这些东西都需要使用一个叫`intent`的东西（关于`intent`的内容会在另外的文章讲），以`startActivity()`方法为例，我们一路向上追溯，可以发现启动`activity`最终是由`AcitivityManagerNative.getDefault()`的本地方法`startActivity()`执行的：

```java
try {
    intent.migrateExtraStreamToClipData();
    intent.prepareToLeaveProcess();
    int result = ActivityManagerNative.getDefault().startActivity(
        whoThread, who.getBasePackageName(), intent,
        intent.resolveTypeIfNeeded(who.getContentResolver()), token,
        target != null ? target.mEmbeddedID : null, requestCode, 0, null, options);
    checkStartActivityResult(result, intent);
} catch (RemoteException e) {
}
```

这个时候我们发现，传入的`context`已经变成了上面代码中的`who`，利用这个 `context`获取了包名与方法的第四个参数`who.getContentResolver()`。它的作用是提供信息来解析`intent`的[`MIME type`](https://en.wikipedia.org/wiki/Media_type)，帮助系统决定`intent`的目标。

可以看到`context`在这里同样起到了一个提供必要信息的作用。

### Context的作用

在这里再重复一遍上面说过的话，配合之前的例子，是不是可以更好地理解了呢？

>   我们可以把它看作是一个连接我们代码与安卓系统的“桥梁”，我们开发的应用是与运行在设备上的操作系统紧密相关的，只能通过操作系统，我们才能去启动一个新的`Activity`，向其他应用发送广播，启动一个新的`Service`或是访问我们存放在`apk`中的资源文件。
>
>    `Context`就是系统为我们提供上述功能的一个接口，我们需要使用它去完成与系统的信息交换。

## Context的使用

### Context分类

`Context`并不是都是相同的，根据获取方式的不同，我们得到的`Context`的各类也有所不同。

#### `Activity`/`Service`

我们知道`Acitivity`类继承自`ContextThemeWrapper`，`ContextThemeWrapper`继承自`ContextWrapper`，最后`ContextWrapper`继承自`Context`。顾名思义，`ContextWrapper`与`ContextThemeWrapper`只是将`Context`进行了再次的包装，加入了更多的信息，同时对一些方法做了转发。

所以我们在`Activity`或`Service`中需要`Context`时就可以直接使用`this`，因为它们本身就是`Context`。

当系统创建一个新的`Activity`/`Service`实例时，它也会创建一个新的`ContextImpl`实例来封装所有的信息。

**对于每一个`Activity`/`Service`实例，它们的基础`Context`都是独立的。**

#### `Application`

`Application`同样继承于`ContextWrapper`，但是`Application`本身是以单例模式运行在应用进程中的，它可以被任何`Activity`/`Service`用`getApplication()`或是被任何`Context`使用`getApplicationContext()`方法获取。

**不管使用什么方法去获取`Application`，获取的总是同一个`Application`实例。**

#### `BroadcastReciver`

`BroadcastReciver`本身并不是一个`Context`或在内部保存了一个`Context`，但是系统会在每次调用其`onRecive()`方法时向它传递一个`Context`对象，这个`Context`对象是一个`ReceiverRestrictedContext`（接收器限定`Context`），与普通`Context`不同在它的`registerReceiver()`与`bindSerivce()`方法是被禁止使用的，这意味着我们不能在`onRecive()`方法中调用该`Context`的这两个方法。

**每次调用`onReceive()`方法传递的`Context`都是全新的。**

#### `ContentProvider`

它本身同样不是一个`Context`，但它在创建时会被赋予一个`Context`并可以通过`getContext()`方法获取。

**如果这个内容提供器运行在调用它的应用中，将会返回该应用的`Application`单例，如果它是由其他应用提供的，返回的`Context`将会是一个新创建的表示其他应用环境的`Context`。**

### 使用`Context`时的陷阱

现在我们知道`Context`的几种分类，其实上面的分类也就是我们获取它的方式。着重标出的内容说明了它们被提供的来源，也暗指了它们的生命周期。

我们常常会在类中保存对`Context`的引用，但是我们要考虑生命周期的问题：如果被引用的这个`Context`是一个`Acitivity`，**如果存放这个引用的类的生命周期大于`Activity`的生命周期，那么`Activity`在停止使用之后还被这个类引用着，就会引致无法被GC，造成事实上的内存泄露。**

举一个例子，如果使用下面的一个单例来保存`Context`的引用来加载资源：

```java
public class CustomManager {
    private static CustomManager sInstance;
 
    public static CustomManager getInstance(Context context) {
        if (sInstance == null) {
            sInstance = new CustomManager(context);
        }
 
        return sInstance;
    }
 
    private Context mContext;
 
    private CustomManager(Context context) {
        mContext = context;
    }
}
```

这段程序的问题在于不知道传入的`Context`会是什么类型的，可能在初始化的时候传入的是一个`Activity`/`Serivce`，那么几乎可以肯定的是，这个`Activity`/`Service`将不会在结束以后被垃圾回收。如果是一个`Activity`，那么这意味着与它相关联的`View`或是其他庞大的类都将留在内存中而不会被回收。

为了避免这样的问题，我们可以改正这个单例：

```java
public class CustomManager {
    private static CustomManager sInstance;
 
    public static CustomManager getInstance(Context context) {
        if (sInstance == null) {
            //Always pass in the Application Context
            sInstance = new CustomManager(context.getApplicationContext());
        }
 
        return sInstance;
    }
 
    private Context mContext;
 
    private CustomManager(Context context) {
        mContext = context;
    }
}
```

我们只修改了一处，第7行中我们使用`context.getApplicationContext()`这个方法来获取`Application`这个单例，而不是直接保存`context`本身，这样就可以保证不会出现某`context`因为被这个单例引用而不能回收的情况。而`Application`本身是单例这个特性保证了生命周期的一致，不会造成内存的浪费。

### 为什么不总是使用`application`作为`context`

既然它是一个单例，那么我们为什么不直接在任何地方都只使用它呢？

这是因为各种`context`的能力有所不同：

![](/images/context01.png)

（图片出处见文末）

对几个注解的地方作说明：

1.  一个`application`可以启动一个`activity`，但是需要新建一个`task`，在特殊情况下可以这么做，但是这不是一个好的行为因为这会导致一个不寻常的返回栈。
2.  虽然这是合法的，但是会导致填充出来的`view`使用系统默认的主题而不是我们设置的主题。
3.  如果接收器是`null`的话是被允许的，通常在4.2及以上的版本中用来获取一个粘性广播的当前值。

我们可以发现与`UI`有关的操作除`activity`之外都不能完成，在其他地方这些`context`能做的事情都差不多。

但是我们回过头来想，这三个与`UI`相关的操作一般都不会在一个`activity`之外进行，这个特性很大程度上就是系统为我们设计成这样的，如果我们试图去用一个`Application`去显示一个`dialog`就会导致异常的抛出和应用的崩溃。

对上面的第二点再进一步解释，虽然我们可以使用`application`作为`context`去填充一个`view`，但是这样填充出的`view`使用的将会是系统默认的主题，这是因为只有`acitivity`中才会存有我们定义在`manifest`中的主题信息，其他的`context`将会使用默认的主题去填充`view`。

### 如何使用正确的`Context`

既然我们不能将`Activity`作为`context`保存在另外一个比该`Activity`生命周期长的类中，那么如果我们需要在这个类中完成与`UI`有关的操作（比如显示一个`dialog`）该怎么办？

如果真的遇到了这样的情况：我们不得不保存一个`activity`在一个比该`Activity`生命周期长的类中以进行`UI`操作，就说明我们的设计是有问题的，系统的设计决定了我们不应该去进行这样的操作。

所以我们可以得出结论：

我们应该在`Activity`/`Service`的生命周期范围内直接使用该`Activity`/`Service`作为`context`，在它们的范围之外的类，应该使用`Application`单例这个`context`（并且不应该出现`UI`操作）。

## Reference

[https://possiblemobile.com/2013/06/context/](https://possiblemobile.com/2013/06/context/)

[https://web.archive.org/web/20170621005334/http://levinotik.tumblr.com/post/15783237959/demystifying-context-in-android](https://web.archive.org/web/20170621005334/http://levinotik.tumblr.com/post/15783237959/demystifying-context-in-android)

[http://grepcode.com/file/repository.grepcode.com/java/ext/com.google.android/android/5.1.1_r1/android/app/ContextImpl.java?av=f](http://grepcode.com/file/repository.grepcode.com/java/ext/com.google.android/android/5.1.1_r1/android/app/ContextImpl.java?av=f)
