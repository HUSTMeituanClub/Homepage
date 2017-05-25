Title: Android Google官方MVP架构分析
Date: 2017-05-25 20:54:08
Tags: android, MVP, architecture
Authors: Di Wu
Category: Android

## 写在前面

关于MVP模式的基本介绍与优缺点可以参见下面这篇文章：

>   https://segmentfault.com/a/1190000003927200

本文的重点是对Google官方写的一个MVP架构实现的Demo进行简单的分析来看看谷歌实现的Android MVP架构是怎么搭建的。

谷歌官方的架构Demo地址：

>   https://github.com/googlesamples/android-architecture

本文所讲解的为：

>   https://github.com/googlesamples/android-architecture/tree/todo-mvp

需要读者参照源码查看本文。

我将这个todo应用的框架提炼出来（同时也意味着丢失了很多的实现细节，但可以将架构看得更加清晰），制作了一张伪`UML`图（为了简化，没有遵循`UML`的规范），下面我们参照着表中的内容进行分析：

<!--more-->

<img src="/images/android_mvp_uml.jpg">


## BaseView与BasePresenter

可以看到它们是独立于包外的两个基础接口，之后的所有`View`与`Presenter`接口都将继承它们，所以应该将一些通用的方法写在这两个`Base`接口中。

## tasks包

整个app中`tasks`、`taskdetail`、`statistics`三个包对应着的就是三个`Activity`，可以看到每一个包中包含了对应的`Activity`、`View` 、`Presenter`与`Contract`类和其他工具组件，通过这样的方式构成了应用的一个组成单元（每一个`Activity`与其对应的`View`和实现逻辑的`Presenter`）。

图中我只展现了`tasks`这一个包，其他的包内部的结构也是一样的。

### TasksContract接口

`TasksContract`接口包含两个接口，分别是继承了`BaseView`与`BasePresenter`的`View`与`Presenter`。

我们可以将`Contract`接口视为管理`View`与`Presenter`需要实现的方法的汇总接口，这些方法在实例类中实际上都是通过接口来进行调用的，这样就可以避免依赖于某一个特定类的方法来进行处理，从而可以有多种实现`View`与`Presenter`的方式，便于进行单元测试（可以看到源代码中就有很多单元测试的内容，但是在这篇文章中我们将它们忽略）。

一切与更新UI有关的逻辑都应该放在`TasksContract.View`接口中。

一切与业务有关的逻辑都应该放在`TaskContract.Presenter`接口中。

### TasksFragment与TasksPresenter

`TasksFragment`与`TaskPresenter`分别是`TasksContract.View`与`TaskContract.Presenter`接口的实例。

`TaskActivity`在初始化时会先创建`TasksFragment`实例，再将其作为构造参数传递给`TaskPresenter`，`TaskPresenter`在构造方法中又会调用`TasksFragment`的`setPresenter`方法将自身传递给`TasksFragment`。这样`Presenter`与`View`就分别存有了一份对方的引用。

构造完成后，当用户与UI进行交互，`View`一律调用`Presenter`的相关方法来进行交互事件的处理或请求数据更新。如果有新的内容需要呈现在UI上，则由`Presenter`调用`View`的相关方法来进行更新。`Presenter`则负责与上一级的数据存储池进行交互来更新数据或是获取新的数据。

可以看到`Presenter`充当了一个“中介”，`View`的所有请求都将交由`Presenter`进行处理，而`View`现在需要做的只有提供相应方法供`Presenter`进行调用，避免了将大量业务逻辑写在`View`中。同时也避免了`View`与数据的直接交互，而是由`Presenter`“单线操作”，降低了耦合度。

## Data包

### Task

这里的`Task`是一个[`POJO`](https://en.wikipedia.org/wiki/Plain_old_Java_object)类，用于表示储存的数据。

### source包

#### TaskDataSource接口

`TaskDataSource`接口定义了所有可以的用于操作数据的对象的方法，换句话说，无论数据的来源是什么，我们都可以通过调用实现了这个接口的对象的方法来操纵数据。

#### GetTaskCallback与LoadTasksCallback

注意到用于获取数据的方法的参数都利用了`callback`进行回调来传递数据。这样做主要因为数据的获取有可能是异步的，使用回调机制可以避免线程因为等待数据而阻塞。

#### local包与remote包

这两个包分别存放着一个实现了`TaskDataSource`接口的类，他们就代表了从本地缓存获取数据与从远端获取数据。当然与获取数据有关的其他类也应该放在这个包下。

#### TaskRepository

有了从本地与远端获取数据的类，那么就应该有一个类对它们进行管理，我们希望的是有本地缓存时读取本地缓存，没有时就从远端的获取数据。在更为复杂的情况下，我们需要处理来自远端的请求并与本地的数据进行同步。

`TaskRepository`就是用于管理所有的这些数据来源并统一成一个`TaskDataSource`暴露给`Presenter`来操作数据，而这些数据管理逻辑就被隐藏在了`TaskRepository`中。

值得注意的是，源码中在`TaskRepository`中还实现了一个内存缓存，可以避免从其他两个低速来源中获取数据。
