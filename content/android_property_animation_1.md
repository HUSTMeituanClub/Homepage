Title: Android PropertyAnimation 属性动画（一）初探
Date: 2017-03-10 14:14:45
Category: Android
Tags: android, UI, animation 
Authors: Di Wu


## 前言

相对于静态的页面，动画往往能更直观地表达所需的信息，在UI开发过程中起着相当大的作用。

Android为我们提供了一系列实现动画效果的方法，`PropertyAnimaiton`是最常见也是最实用的一种，如同它的名字一样，它的实现方式是通过改变对象的一系列属性值来改变对象的状态， 例如动态地改变绘制的位置就可以实现绘制物体的移动效果，动态地改变对象的显示状态可以实现闪烁效果。

## Animator概览

Android提供的实现属性动画的工具是`android.animation.Animator`这个类，它的使用需要配合`animation`包下的其他工具类，这个类的功能是什么，我们要如何使用它来实现属性动画呢？

<!--more-->

我们可以将`Animator`理解为`Android`为我们提供的一个按我们的需要在一定时间段内**连续地**计算并返回值的工具，这个值可以是通用的整型、浮点型，也可以是我们自定义的类型。

我们可以设置返回值的范围，并可以控制值变化的快慢，例如实现自由落体下落的物体时我们需要让高度值以一个越来越快的速度降低。

这里的连续需要注意，实际上是不可能产生真正意义上的连续值的，但是如果**在绘制过程中计算这个值的速度小于绘制一帧所需要的时间**，那么我们就可以在视觉上认为这个值是在连续改变的。这一点也是理解其作用的关键：我们很难去写出一个可以随时获取连续值的工具，而`Animator`正是一个满足我们这个需求的一个通用工具。

通过将`Animator`与`View`的绘制过程结合，就可以实现绝大多数的动画效果， 但是`Animator`也不只局限在使用在绘制动画，只要是有相似需求的地方都可以使用它来实现， 同时由于属性动画只针对属性进行修改，与被修改对象之前几乎没有耦合，不需要对被修改对象作出改变，可以设置方式也多种多样，这些都是动画的另一种实现方法`ViewAnimator`所无法做到的，所以我属性动画是现在实现动画效果的普遍做法。

## 使用Animator

### Animator子类

下面就来看看如何使用`Animator`满足我们的需求。

我们使用`Animator`可以分为两个步骤，一是进行数值的计算，二是将计算出的数值设置到对应的对象上。而`Animator`有着三个子类：`ValueAnimator` `ObjectAnimator` `AnimatorSet`。

*   `ValueAnimator`实现了上述过程的第一个步骤：进行数值的计算。第二个步骤则需要我们重写它的回调在值发生改变时候手动地为对象更新属性值。
*   `ObjectAnimator`则在其基础上进行了进一步的封装，加入了一些方法使得它可以绑定一个对象，在数值改变的同时对对象的属性进行更新。
*   `AnimatorSet`可以对`Animator`进行组合，让它们之间进行联动，例如可以设置一个动画根据另一个动画的状态来决定是否开始、暂停或停止。

可以看到，`ValueAnimator`提供了一个`Animator`最核心的内容，也是使用中最为灵活的一个。`ObjectAnimator`由于绑定了相应的对象，在使用上会受一些限制。`AnimatorSet`专用于需要组合动画的场景。

### ValueAnimator

在这篇博客中，我们关注最为核心的`ValueAnimator`。

#### 关键属性

`ValueAnimator`对象内部维护了一系列属性来保存所需的各种信息。

*   `Duration`：动画的持续时间，通过`setDuration()`方法设置
*   `Repeat count and behavior`：重复计数与重复模式，我们可以通过设置这两个属性来控制动画是否重复以及重复的次数，通过`setRepeatCount()`与`setRepeatMode()`方法设置
*   `Frame refresh delay`：帧刷新延迟，也就是计算两帧动画之间的间隔时间，但这个时间只是`Animator`尽力去保持的值，具体的间隔时间会由于系统负载与性能的不同而不同，同时设置它的方法为一个静态方法：`ValueAnimator.setFrameDelay()`，会被设置到所有的`Animator`上，这是因为这些`Animator`都在同一个时间循环中。这个属性也有可能会被忽略如果动画系统采用了内部的计时来源，例如`vsync`来计算属性。同时这个方法需要在与`start()`方法相同的进程中调用
*   `Time interpolation`：时间插值器，是我们实现不同动画效果的关键，每一时刻所返回的数值由它决定，后文会详细讲

#### 初始化与TypeEvaluator

`ValueAnimator`对象的构造函数只由内部使用，获取`ValueAnimator`对象的方法是调用它的工厂方法：

`ValueAnimator.ofArgb()`

`ValueAnimator.ofInt()`

`ValueAnimator.ofFloat()`

`ValueAnimator.ofObject()`

`ValueAnimator.ofPropertyValuesHolder()` //本篇未涉及，下一篇进行讲解

前三个可以看作是`ValueAnimator`为我们提供的初始化方式，它们的参数都是对应类型的长度可变参数:`(Type ...values)`，我们需要提供一个以上的参数，`ValueAnimator`最终提供的值会在这些值之前变动。

一般情况下这里提供的`Argb`（用于颜色值的变化）和整型、浮点值基本可以满足我们的需求，但是某些时候我们需要结果是我们自定义的一些对象，这个时候就需要用到`TypeEvaluator<>`接口了，与这个接口对应的工厂方法是`ValueAnimator.ofObject()`：

```java
ValueAnimator ofObject (TypeEvaluator evaluator, 
                Object... values)
```

这里的可变参数类型变为了`Object`，同时还需要我们提供一个`TypeEvaluator<>`，用于“告诉”`Animator`如何返回这个`Object`值。

---

`TypeEvaluator<>`接口并不复杂，只有一个方法需要我们重写：

```java
T evaluate (float fraction, 
                T startValue, 
                T endValue)
```

`startValue`与`endValue`非常好理解，就是我们在获取`Animator`时指定的值的起始值和结束值。类型与返回类型一致，当然都是我们自定义的类型。

这里的`fraction`就是决定我们最终返回值的关键参数。我们可以把这个`fraction`理解为`animator`提供给我们的最终的数值改变的比例，以小数表示，小于0表示低于`startValue`，大于0表示超出`endValue`，0-1之间表示在`startValue`与`endValue`之间。我们要做的就是把这个值转换为在起始和结果范围之间的合适的对象值。

例如，对于基本的浮点类型，默认的`FloatEvaluator`是这样的：

```java
    public Float evaluate(float fraction, Number startValue, Number endValue) {
        float startFloat = startValue.floatValue();
        return startFloat + fraction * (endValue.floatValue() - startFloat);
    }
```

可以看到，就是相当于把`fraction`所表示的比例“投射”到了我们所需要的数据对象上，这里是浮点类型。如果使用我们的自定义类型，我们必须为自己的类型定义这样的操作。

**注意：**这里要求我们必须将`fraction`**线性**地反应到对应的类型上，因为`fraction`反映的是最终的动画进度，我们必须如实地按照这个进度改变我们的属性，所以需要将result = x0 + t * (x1 - x0)`这样的形式反映到我们自己的对象上。

自定义了`TypeEvaluator`以后就可以作为参数使用在上面的`obObject()`工厂方法中了。

#### 插补细分器(`Interpolators`)

下面介绍使用`ValueAnimator`控制值变化过程中最为重要的一个概念：插补细分器(`Interpolators`)。

它实际上是一个关于时间的函数， 根据时刻的不同来返回不同的值，进而来控制最后的输出的值。那么它是如何表示的呢？

系统为我们提供了一系列预置的`Interpolators`，以较常用的`LinearInterpolater`为例，顾名思义，它是一个线性的插补细分器，意味着输入与输出呈线性关系：

```java
public float getInterpolation(float input) {
    return input;
}
```

输入输出的关键函数就是这个`getInterpolation()`了，可以看到，参数与返回值都是`float`类型，`input`的值在0-1之间，结合前面，我们可以很容易理解，这个`input`就是一个以0-1之间的小数表示的过去的时间值，例如整个动画是1000ms，当`input`为0.25的时候意味着现在的时间过去了250ms。

而返回值就是经过我们的转换，表示出的动画应该进行的时间的比例，这里由于是线性的，所以可以直接返回`input`，这个值最后会到哪里呢？自然就是给我们前面介绍的`TypeEvaluator`。下面一段源码展示了这个过程：

```java
if (mInterpolator != null) {
    fraction = mInterpolator.getInterpolation(fraction);
}
return mEvaluator.evaluate(fraction, mFirstKeyframe.getValue(),
        mLastKeyframe.getValue());
```

作为`getInterpolation()`参数的`fraction`代表着过去的时间比例，这里调用我们设置的`Interpolator`来更新这个`fraction`，现在这个`fraction`表示的就是动画已经进行的比例，下一步就要根据它来获取对应的对象值（调用了我们之间谈到过的`evaluate()`方法，这里的`KeyFrame`的概念会在之后的博客讲到），后面的两个参数就是传递给`evaluate`的起始与结束范围。

最终，我们就获得了一个按照我们设定的`Interpolator`返回的动画属性值。

如果想要实现加速效果呢？Android同样为我们提供了现成的`AccelerateInterpolator`：

```java
public float getInterpolation(float input) {
    if (mFactor == 1.0f) {
        return input * input;
    } else {
        return (float)Math.pow(input, mDoubleFactor);
    }
}
```

同样很简洁，这里用到了`mFactor`与`mDoubleFactor`分别表示我们在构造函数里面设置的指数值：

```java
public AccelerateInterpolator(float factor) {
    mFactor = factor;
    mDoubleFactor = 2 * mFactor;
}
```

如果我们设置的为1，会返回`input`的平方，其他值则会返回`input`的`mDoubleFactor`次方，使得动画属性可以以不同的函数曲线形式变化。

如果我们要实现自己的`Interpolator`呢？只需要实现`TimeInterpolator`接口，这个接口只需要我们实现一个`getInterpolation`方法。我们可以根据`input`值返回不同的值来返回不同的值表示动画的进度。

**注意：**返回值的范围不一定要在0-1之间，小于0或大小1的值可以表示超出预设范围的目标值。

这篇博客到此结束，在下一篇博客中将会以一个绘制自由落体的弹跳小球的示例来演示如何使用`Animator`与介绍它的回调函数。
