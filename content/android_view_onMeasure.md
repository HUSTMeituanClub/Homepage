Title: Android View绘制之measure过程
Date: 2017-03-10 18:30:16
Category: Android
Tags: android, view
Authors: Di Wu


[上一篇博客](http://www.viseator.xyz/2017/03/09/android_view_lifeCycle/)简单地介绍了`View`绘制的生命周期， 从这篇博客开始将会对这个周期中一些有用的过程进行一个详细一些的介绍。这篇的主角就是在构造方法之后调用的`measure`过程。

为了演示，继承了`TextView`来实现一个自定义的`View`。注意这里继承的应该是`android.support.v7.widget.AppCompatTextView`这个类。同时为了`xml`文件的正常解析，我们需要实现`View`的三个构造方法。

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

再通过完整包名的方法在`xml`布局文件中创建我们的`View`就可以直接显示了。

```xml
<com.viseator.viewtest.VView
    android:layout_width="100dp"
    android:layout_height="100dp"
    android:background="@color/Gray"
    />
```

这里给了`TextView`一个背景颜色便于后面的观察。

---

下面就开始分析`measure`过程。

`measure`是一个自顶向下的过程，即父`View`会依次调用它的子`View`的`measure()`方法来对它的子`View`进行测量。

`View`的`measure()`方法最终会调用`onMeasure()`，真正的尺寸信息就是在`onMeasure()`方法中最终确定的。所以我们需要做的就是在自定义`View`中重写`onMeasure()`方法。

那么子`View`根据什么来确定自己应该具有的尺寸呢？当然不可能让子`View`自由地决定自己的大小，父`View`必然需要向子`View`传递信息来帮助子`View`来确定尺寸，而子`View`则必须满足父`View`的要求。查看`measure()`的方法签名：

```java
public final void measure(int widthMeasureSpec, int heightMeasureSpec)
```

这里的`widthMeasureSpec`与`heightMeasureSpec`就是存储这一信息的参数。它们的类型是`int`，内部以高两位来存储测量的模式，低三十位为测量的大小，计算中使用了位运算来提高并优化效率。当然我们不必使用位运算来获得对应的数值，`View.MeasureSpec`为我们提供了对应的方法。

测量模式有三种：

*   `EXACTLY`：精确值模式，即子`View`必须使用这一尺寸，并且保证它们的所有后代都在这个范围之内。当我们将控件的`layout_width`、`layout_height`属性指定为具体数值或`match_parent`时，系统使用这一模式。
*   `UNSPECIFIED`：无限制模式，不对子`View`施加任何限制，完全由子`View`决定自己的大小。可以用于查看子`View`想要的尺寸，比如可以把子`View`的长度使用`EXACTLY`模式限制在100，不限制宽度来查看子`View`在长度为100情况想要的宽度。
*   `AT_MOST`：最大值模式，只限制子`View`能具有的最大尺寸，子`View`必须保证它和它的后代们都在这一范围之内。

了解这些，我们就可以通过重写`onMeasure()`来确定一个`View`的尺寸。

但在重写方法时要注意：必须调用`setMeasuredDimension()` 来将最终尺寸存储在`View`中，否则会抛出一个`IllegalStateException`。

`xml`:

```xml
<com.viseator.viewtest.VView
    android:layout_width="wrap_content"
    android:layout_height="100dp"
    android:background="@color/Gray"
    />
```

`VView`:

```java
@Override
protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
    int widthMode = MeasureSpec.getMode(widthMeasureSpec);
    int heightMode = MeasureSpec.getMode(heightMeasureSpec);
    int width = MeasureSpec.getSize(widthMeasureSpec);
    int height = MeasureSpec.getSize(heightMeasureSpec);
    Log.d(TAG, "widthMode: " + widthMode);
    Log.d(TAG, "heightMode: " + heightMode);
    Log.d(TAG, "width :" + width);
    Log.d(TAG, "height :" + height);
    super.onMeasure(widthMeasureSpec, heightMeasureSpec);
```

log:

![output](/images/onMeasureOutput1.png)

这段简单的代码验证了之前的说法，分别对宽高设置了`wrap_content`和固定值，可以发现模式分别为`AT_MOST`与`EXACTLY`（以数值表示）。

这里输出的宽高值是以像素为单位的，可以看到高度的期望值就是设置的大小，但`wrap_content`期望的宽度值为1080（屏幕宽度），默认即为屏幕宽度，但最终计算得出的宽度值由于里面没有文字所以为0。

同样地，`UNSPECIFIED`模式给出的默认尺寸也是屏幕的宽/高。

所以我们可以看到如果想要实现`wrap_content`的效果，我们必须在`onMeasure`中对`AT_MOST`模式计算其内容宽/高并作为最终的宽/高，否则将以屏幕的宽/高进行填充。以`LinearLayout`的源码为例：

```java
if (useLargestChild &&
        (heightMode == MeasureSpec.AT_MOST || heightMode == MeasureSpec.UNSPECIFIED)) {
    mTotalLength = 0;

    for (int i = 0; i < count; ++i) {
        final View child = getVirtualChildAt(i);
        if (child == null) {
            mTotalLength += measureNullChild(i);
            continue;
        }

        if (child.getVisibility() == GONE) {
            i += getChildrenSkipCount(child, i);
            continue;
        }

        final LinearLayout.LayoutParams lp = (LinearLayout.LayoutParams)
                child.getLayoutParams();
        // Account for negative margins
        final int totalLength = mTotalLength;
        mTotalLength = Math.max(totalLength, totalLength + largestChildHeight +
                lp.topMargin + lp.bottomMargin + getNextLocationOffset(child));
    }
}

// Add in our padding
mTotalLength += mPaddingTop + mPaddingBottom;

int heightSize = mTotalLength;
```

这部分代码向我们展示了`LinearLayout`处理子`View`并计算所有的高度的情况。

知道了这个调用过程，我们就可以真正地进行`onMeasure()`的重写了。

例如可以暴力指定`View`尺寸：

```java
    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        setMeasuredDimension(100,600);
    }
```

可以为`AT_MOST`与`UNSPECIFIED`模式指定一个默认大小：

```java
@Override
protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
    setMeasuredDimension(measureSize(widthMeasureSpec), measureSize(heightMeasureSpec));
}

int measureSize(int measureSpec) {
    int mode = MeasureSpec.getMode(measureSpec);
    int size = MeasureSpec.getSize(measureSpec);
    if (mode == MeasureSpec.EXACTLY) {
        return size;
    } else {
        size = 300; //Default size
        return Math.min(size,MeasureSpec.getSize(measureSpec));
    }
}
```

至于更复杂的计算逻辑由于本人能力有限就不写demo了，如果以后实际中遇到需要的时候再作补充。
