Title: Android PropertyAnimation 属性动画（二）弹跳小球实例
Date: 2017-04-02 10:08:31
Category: Android
Tags: android, UI, animation
Authors: Di Wu

## 前言

[GitHub完整代码](https://github.com/viseator/AndroidAnimatorBounceBallDemo)

[上篇博客](http://www.viseator.com/2017/03/26/android_property_animation_1/)简单介绍了属性动画的原理，这篇博客将会以一个简单的实例来运用上之前讲的内容，并对`Animator`的几个回调方法进行讲解。

目标是自定义一个`View`，在画布上绘制一个小球，点击屏幕后小球从顶部自由下落，落到底边后反弹，反弹损失一半的能量，也就是说小球只能上升到下落时一半的高度，再重复这个过程直到退出程序。如图：

![](/images/android_animator.gif)

<!--more-->

## 创建自定义View

首先我们要创建一个自定义`View`，这里我就采用继承`LinearLayout`的方式来创建这个`View`，但要注意`LinearLayout`默认是不绘制自身的，需要在`onDraw()`方法之前适当的时候调用`setWillNotDraw(false);`令其进行绘制。

在继承`LinearLayout`的同时我们要实现全部三个构造方法，否则xml文件的预览解析会出现问题：

```java
public VView(Context context) {
    super(context);
}

public VView(Context context, AttributeSet attrs) {
    super(context, attrs);
}

public VView(Context context, AttributeSet attrs, int defStyleAttr) {
    super(context, attrs, defStyleAttr);
}
```
创建好自定义`View`后，我们就可以在对应的layout xml布局文件中用完整包名+类名的方式使用我们的自定义`View`：

```xml
<com.viseator.viewtest.VView
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    />
```
同时，我们在绘制之前的`onMeasure()`方法中调用`setWillNotDraw(false);`使自定义`View`可以绘制：

```java
@Override
protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
    setWillNotDraw(false);
    setOnClickListener(this);
    super.onMeasure(widthMeasureSpec, heightMeasureSpec);
}
```
这里也调用了`setOnClickListener()`注册之后的点击事件。

## 绘制

### 小球的绘制

```java
private ValueAnimator animator;
public static final int radius = 50;
private int xPos = radius;
private int yPos = radius;
private Paint paint = new Paint();

@Override
protected void onDraw(Canvas canvas) {
    super.onDraw(canvas);
	if (animator == null) {
		canvasHeight = canvas.getHeight() - radius;    		
		paint.setColor(getResources().getColor(R.color.Gray));
		paint.setAntiAlias(true);
	}
    drawCircle(canvas);
}

void drawCircle(Canvas canvas) {
	canvas.drawCircle(xPos, yPos, radius, paint);
}
```
这里第10行对是否是第一次绘制进行判断并将画布大小保存到`canvasHeight`供之后的绘制使用（之后的绘制的坐标需要相对于画布的坐标）并设置`paint`的属性。

`drawCircle()`方法也非常简单，只是调用`canvas`提供的`drawCircle()`方法指定位置与半径和之前设置的`paint`，调用后就会在屏幕上的对应位置绘制一个小球。

### 下落动画的绘制

下面就要让小球“动”起来，其实并不是小球发生了移动，只是我们不停地改变小球绘制的位置，当绘制的速率（帧率）大于24帧时的，就在视觉上变成了流畅的动画。也就是说，我们需要使用`Animator`连续地改变小球的位置，为了实现加速的效果，位置的改变速率应该随时间增加，也就是需要我们上一篇博客提到的`Evaluator`来实现。

#### animator的初始化

```java
void init(int start, int end) {
    animator = ValueAnimator.ofInt(start, end);
    animator.setDuration(1000);
    animator.setRepeatCount(ValueAnimator.INFINITE);
    animator.setRepeatMode(ValueAnimator.RESTART);
    animator.setInterpolator(new AccelerateInterpolator(rate));
    animator.addUpdateListener(this);
    animator.addListener(this);
}
```
写成一个初始化方法便于重新初始化。

第2行将传入的值区间的开始与结束值作为参数获得了一个值为`int`的`ValueAnimator`。

第3行设置了动画的时间为1秒。

第4、5行分别设置了动画的重复次数为无限次，重复模式为重新开始，顾名思义，动画可以重复进行，重新开始的重复模式意味着一次动画结束之后数值重新从`start`到`end`进行改变，也可以设置重复的模式为反向，即一次动画结束之后数值从`end`到`start`变化。

第六行为`animator`设置了一个库中提供的`AccelerateInterpolator`即加速插值器，这就是我们实现加速效果的关键，上篇之中已经看过它的源码，默认时返回的最终动画进行百分比是时间百分比的平方，达到了位置随着时间的平方变化，也就是实现了加速下落的效果。

第7、8两行分别为`animator`设置了一个`UpdateListener`用于监听数值变化，一个`Listener`用于监听`animator`本身开始、停止、重复。

#### 完成下落动画

创建好了`ValueAnimator`，下一步就是在适合的时候在画布上重新绘制位置参数被`animator`改变后的小球。注意到我们之前小球的y坐标存储在`yPos`变量中，我们只要适时令`yPos`等于改变后的值再通过`invalidate()`方法进入`onDraw()`方法让`View`按小球的参数重新进行绘制就可以了。

`animator`的`ValueAnimator.AnimatorUpdateListener`为我们提供了一个及时刷新`View`的时机，之前为`animator`注册一个`UpdateListener`之后，每当`animator`的值发生改变时，`onAniamtionUpdate()`就会被回调。

那我们就可以在这个回调方法中为`yPos`设置新的值并令`View`重新绘制：

```java
@Override
public void onAnimationUpdate(ValueAnimator animation) {
    yPos = (int) animation.getAnimatedValue();
    invalidate();
}	
```
这样，我们只要启动`animator`令它的值开始变化，就会不断地调用`onAnimationUpdate()`重绘`View`：

```java
@Override
public void onClick(View v) {
    init(radius, canvasHeight);
	animationHeight = canvasHeight + radius;
    animator.start();
}
```
`start()`方法令`animator`开始。

到这里，我们已经可以看到点击屏幕后小球下落到底部并停止的效果。

### 回弹效果实现

我们之前已经为`animator`设置了无限重复，并且模式为重新开始，那么要做到回弹的效果，就要在小球落到底边（动画完成）之后，为小球设置新的初始值与最终值，让小球从最低点回到落下时一半的高度。高度数据我们在`onClick()`中的第4行（上面代码）已经初始化为了相对于画布的高度，之后再使用时只需把它除2就可以表示圆心距底边的高度了。

`Animator.AnimatorListener`为我们提供了一系列方法用于监听`animator`状态的变化（而不是数值）：

![](/images/AnimatorListener.jpg)

（除金色为Android 8新增外），依次为动画取消，动画结束，动画开始重复，动画开始。

这里我们就需要在`onAnimationReapt()`回调中为动画设置新的初值与结束数值：

```java
@Override
public void onAnimationRepeat(Animator animation) {
    ValueAnimator vAnimation = (ValueAnimator) animation;
    if (isDown) {
        animationHeight = (int) (animationHeight * 0.5);
    }
    isDown = !isDown;
    if (isDown) {
        vAnimation.setIntValues(canvasHeight - animationHeight, canvasHeight);
        vAnimation.setInterpolator(new AccelerateInterpolator());
    } else {
        vAnimation.setIntValues(canvasHeight, canvasHeight - animationHeight);
        vAnimation.setInterpolator(new DecelerateInterpolator());
    }
}
```
回调参数中的`animation`就是回调这个函数的`animator`，第3行对其进行一个类型转换。

这里我们使用了一个`isDown`参数来判断是否是下落过程，如果上个动画是下落过程，就将`animationHeight`减半。

第7行把`isDown`置反，再根据`isDown`的判断使用`setIntValues()`方法为`animator`设置新的范围，使用`setInterpolator()`方法设置新的插值器，注意上升时使用的应该是`DecelerateInterpolater`减速上升。

这样在新的动画开始时属性改变的范围就得到了改变，也就使得小球可以反弹了。

为了让每一次点击时动画都可以重新开始，在`onClick()`方法中加入几行初始化代码：

```java
@Override
public void onClick(View v) {
    if (animator != null) {
        animator.end();
    }
    init(radius, canvasHeight);
    animationHeight = canvasHeight + radius;
    isDown = true;
    animator.start();
}
```
这里第3-5行让如果存在的`animator`停止，否则新动画无法启动。

下篇博客将会从源码角度继续探索`animator`的实现原理和更高级的一些特性。

[GitHub完整代码](https://github.com/viseator/AndroidAnimatorBounceBallDemo)
