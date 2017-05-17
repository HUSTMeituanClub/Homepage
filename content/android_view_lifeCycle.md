Title: Android View绘制生命周期总览
Date: 2017-03-09 17:22:41
Category: Android
Tags: Android, View, LifeCycle
Authors: Di Wu

为了直观表示整个过程，我制作了一张流程图。注意以下只是整个生命周期中比较常用的方法，并不代表所有的过程。

![viewLifeCircle](/images/viewLifeCircle.png)

当一个`Activity`收到焦点即将要处于激活状态时，将会被要求绘制它的布局，绘制布局之前的过程在这里不涉及，我们从绘制`View`开始分析。

每个`Activity`被要求提供一个`ViewGroup`作为View树的根，也就是我们熟悉的`setContentView`方法。

```java
    @Override
    public void setContentView(@LayoutRes int layoutResID) {
        getDelegate().setContentView(layoutResID);
    }

    @Override
    public void setContentView(View view) {
        getDelegate().setContentView(view);
    }

    @Override
    public void setContentView(View view, ViewGroup.LayoutParams params) {
        getDelegate().setContentView(view, params);
    }
```

可以看到`setContentView`拥有三种形式，可以直接传入`View`、传入一个`layout`资源文件，或传入一个`View`文件和一个用于提供参数的`LayoutParams`对象。

整个过程将从这个根`View`开始，并遍历它的子`View`来逐一绘制，每个`ViewGroup`承担了要求它的子`View`进行绘制的责任，每个`View`承担了绘制自身的责任。并且父`View`会在子`View`完成绘制之前进行绘制，同级的`View`将以它们出现在树中的顺序进行绘制。

---

首先调用的当然是`View`的构造函数，构造函数分为两种，一种供代码创建的`View`使用，另一种是由`layout`文件生成的`View`使用，区别在于后者会从`layout`文件中读入所有的属性，前者的属性则需要在代码中设置。

另外后者在所有的子`View`都生成完毕之后会回调`onFinishInflate`方法。

---

在正式绘制之前要进行两个过程（布局机制[layout mechanism]）：

首先是`measure`过程。这是一个自顶向下的过程，父`View`将期望尺寸传递给子`View`，子`View`需要根据这一信息确定自己的尺寸，并且保证这一尺寸满足父`View`对其的要求，在子`View`确定自己尺寸的过程中也要向它的子`View`传递信息，就这样递归地确定自己的尺寸信息并储存在自身中，保证在`measure`方法返回时，自身的尺寸信息已经确定。所以在根`View`的`measure`方法返回时，所有子`View`的尺寸信息已经全部确定了。

这个过程需要注意一个`View`可能不止一次地调用`measure`方法来对子`View`进行测量。比如，可能要先传递一个无限制的信息来获取子`View`想要的尺寸，当子`View`希望的尺寸过大或过小时，父`View`需要再次调用`measure`方法来给予子`View`一些限制。

第二个是`layout`过程，这也是一个自顶向下的遍历过程，在这个过程中父`View`负责按照上一个过程中计算并储存在`View`中的尺寸信息来正确地放置子`View`。

同时这个过程可以通过调用`requestLayout()`来重新进行，并且会引起后面步骤的执行，相当于对以这个`View`为根的`View`树进行重新布局。

---

下面就是真正的绘制过程了，也就是`View`的`draw()`方法，在`draw()`方法中，（如果需要）会**依次**调用如下方法：

1.  `drawBackground()`：在画布上绘制特定的背景
2.  `onDraw()`：重写`View`几乎必重写的一个方法，用于绘制图形
3.  `dispatchDraw()`：`ViewGroup`会重写这个方法，用于对所有的子`View`调用`draw()`方法进行绘制
4.  `onDrawForeground()`：用于绘制前景（如果需要）

可以看到如果需要调用上述的方法必定会按照这个顺序进行，也就是说，子`View`的绘制是在父`View`绘制之后进行的，而同级`View`的绘制是根据`View`在父`View`中的顺序进行绘制的。

同时这个过程可以通过调用`invalidate()`来重新进行，相当于进行某个`View`的重绘。
