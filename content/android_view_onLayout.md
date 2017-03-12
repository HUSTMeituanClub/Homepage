Title: Android View绘制之layout过程
Date: 2017-03-12 14:02:47
Categories: Android
Tags: Android, View
Authors: Di Wu


经过[上一篇](http://www.viseator.xyz/2017/03/10/android_view_onMeasure/)介绍的`measure`过程之后，各个`View`的尺寸信息已经存储在了每个`View`中，下面是`layout`过程，`layout`过程的目的是根据上一步中计算出的尺寸来正确设置各个`View`及其后代的位置。这个过程首先被调用的是`View`的`layout()`方法，`layout()`的方法签名是`public void layout(int l, int t, int r, int b) `，四个参数分别为左边界距父`View`左边界的距离，上边界距父`View`上边界的距离，右边界距父`View`左边界的距离，下边界距父`View`上边界的距离。

```java
boolean changed = isLayoutModeOptical(mParent) ?
        setOpticalFrame(l, t, r, b) : setFrame(l, t, r, b);
```

`changed`是用于传递给`onLayout()`方法的参数，它指示了布局是否被改变。

后面的表达式查看了父`View`的布局模式是否需要显示边框，如需要，调用的是`setOpticalFrame()`方法：

```java
private boolean setOpticalFrame(int left, int top, int right, int bottom) {
    Insets parentInsets = mParent instanceof View ?
            ((View) mParent).getOpticalInsets() : Insets.NONE;
    Insets childInsets = getOpticalInsets();
    return setFrame(
            left   + parentInsets.left - childInsets.left,
            top    + parentInsets.top  - childInsets.top,
            right  + parentInsets.left + childInsets.right,
            bottom + parentInsets.top  + childInsets.bottom);
}
```

 可以看到这个方法读取了设置的边框值， 把原值加上边框值后还是调用了`setFrame()`方法。

`setFrame()`方法通过传入的参数确定了该`View`最终的位置以及尺寸。

可以看到，一个`View`最终显示在什么位置以及它的尺寸是由`layout()`方法决定的，`onMeasure()`方法只是将测量出的`View`期望具有的大小储存在`View`中。一般情况下，我们会根据储存的这个尺寸来作为设定的依据。

接下来`layout()`方法会调用`onLayout()`方法，（如果需要的话）我们需要重写这个方法来调用子`View`的`layout()`方法。所以决定子`View`如何显示的关键步骤就在这里，他们的位置和尺寸完全取决于这里调用它们的`layout()`方法时传入的参数。当然一般情况下我们会根据子`View`中的测量结果来设置这个值。这里拿`FrameLayout`这个需要处理子`View`的`ViewGroup`实例来举例：

```java
@Override
protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
    layoutChildren(left, top, right, bottom, false /* no force left gravity */);
}
```

直接调用了`layoutChildren()`：（省略部分行）

```java
void layoutChildren(int left, int top, int right, int bottom, boolean forceLeftGravity) {
    final int count = getChildCount();

    final int parentLeft = getPaddingLeftWithForeground();
    final int parentRight = right - left - getPaddingRightWithForeground();

    final int parentTop = getPaddingTopWithForeground();
    final int parentBottom = bottom - top - getPaddingBottomWithForeground();

    for (int i = 0; i < count; i++) {
        final View child = getChildAt(i);
            final int width = child.getMeasuredWidth();
            final int height = child.getMeasuredHeight();

            int childLeft;
            int childTop;

            switch (verticalGravity) {
                case Gravity.TOP:
                    childTop = parentTop + lp.topMargin;
                    break;
                case Gravity.CENTER_VERTICAL:
                    childTop = parentTop + (parentBottom - parentTop - height) / 2 +
                    lp.topMargin - lp.bottomMargin;
                    break;
                case Gravity.BOTTOM:
                    childTop = parentBottom - height - lp.bottomMargin;
                    break;
                default:
                    childTop = parentTop + lp.topMargin;
            }

            child.layout(childLeft, childTop, childLeft + width, childTop + height);
        }
    }
}
```

省略了与获取布局属性相关的代码，可以看到：

*   4-8行获取了父`View`的位置数据并在18-31行用于确定最终的位置数据
*   10-11行遍历了所有的子`View`
*   12-13行获取了子`View`中在上一步骤的测量过程中储存的宽和高，并用于第33行中设置最终的右边界与下边界
*   第33行调用子`View`的`layout()`方法
