Title: Java泛型中List、List&lt;Object&gt;、List&lt;?&gt;的区别
Date: 2017-02-14 16:30
Tags: Java
Authors: Di Wu
Categories: Java

Java 1.5中引入了泛型的概念以增加代码的安全性与清晰度，同时为了提供对旧代码的兼容性，让旧代码不经过改动也可以在新版本中运行，Java提供了原生态类型（或称原始类型）。但是实际中在新的代码中已经不应该使用原生态类型。

原生态类型的含义是不带任何实际参数的泛型名称，例如Java 1.5后改为泛型实现的`List<E>`，`List`就是它的原生态类型，与没有引入泛型之前的类型完全一致。

而在虚拟机层面上，是没有泛型这一概念的——所有对象都属于普通类。在编译时，所有的泛型类都会被视为原生态类型。

那么为什么不应该使用原生态类型呢？

>   如果使用原生态类型，就失掉了泛型在安全性和表述性方面的所有优势。——Effective Java

泛型的目的简单地说就是可以让一些运行时才能发现的错误可以在编译期间就可以被编译器所检测出，运行时出问题的代价与编译期出现问题的代价的差别可想而知。换句话说，泛型是编译器的一种及时发现错误的机制，同时也给用户带来了代码的清晰与简洁的附加好处（不必再写一些复杂而危险并且不直观的强制类型转换）。

下面就进入正题谈谈以`List`为例时`List`、`List<Object>`、`List<?>`的区别。

先下定义：

*   `List`：**原生态类型**
*   `List<Object>`：**参数化的类型**，表明`List`中可以**容纳**任意类型的对象
*   `List<?>`：**无限定通配符类型**，表示**只能包含某一种未知对象类型**

下面看一段代码：

    #!java
    public class DiffInGeneric {
        public static void main(String[] args) {
            List<String> strings = new ArrayList<>();
            List list = strings;//ok
            List<Object> objects = strings;
            //Error: java: incompatible types: java.util.List<java.lang.String> cannot be converted to java.util.List<java.lang.Object>
        }
    }

我们创建了一个`List<String>`类型的对象`strings`，再把它赋给原生态类型`List`，这是可以的。但是第5行中尝试把它传递给`List<Object>`时，出现了一个类型不相容错误，注意，这是一个编译期错误。

这是因为泛型有子类型化的规则：

`List<String>`是原生态类型`List`的一个子类型。虽然`String`是`Object`的子类型，但是由于**泛型是不可协变的**，`List<String>`并不是`List<Object>`的子类型，所以这里的传递无法通过编译。

如果像上面那样使用原生态类型会有什么隐患呢？看下面一段代码：

    #!java
    public class DiffInGeneric {
        public static void main(String[] args) {
            List<String> strings = new ArrayList<>();
            unsafeAdd(strings, (Integer)1);
            System.out.println(strings.get(0));
        }

        private static void unsafeAdd(List list, Object object) {
            list.add(object);
        }
    }

编译器提示了两条警告：

第8行：

    #!shell
    warning: [rawtypes] found raw type: List
    private static void unsafeAdd(List list, Object object) {
                                  ^
    missing type arguments for generic class List<E>
    where E is a type-variable:
        E extends Object declared in interface List

警告发现了原生态类型`List`，同时还贴心地指出了`List<E>`的形式以及`E`的来源。

第9行：

    #!shell
    warning: [unchecked] unchecked call to add(E) as a member of the raw type List
            list.add(object);
                    ^
     where E is a type-variable:
        E extends Object declared in interface List

同样指出了我们正在把一个对象添加到`List`中，而这个添加过程由于我们使用了原生态类型而无法被检验。

如果忽略这两条警告并运行这个程序，显然会出现一条错误：

第5行： 

    #!java
    Exception in thread "main" java.lang.ClassCastException: java.lang.Integer cannot be cast to java.lang.String

我们试图把一个自动装箱后的`Integer`对象插入到了一个被声明为`List<String>`的`List`中，由于我们在`unsafeAdd`方法中使用了原生态类型，从而使得编译器无法在编译期间检查`add`参数的合法性，从而没有产生编译错误而是产生了一条警告，运行后当试图把这个错误的`Integer`对象作为`String`取出时就会出现`ClassCaseException`异常，这是个运行时的异常，导致了程序中断。

如果我们把`unsafeAdd`方法的参数从`List`改为`List<Object>`会发生什么呢？正如之前所说的那样，由于`List<String>`并不是`List<Object>`的子类型，所以在传递参数的时候就会出现第一段代码中出现的**编译期错误**。这体现了泛型所带来的安全性。

可以这么说，`List<Object>`唯一特殊的地方只是`Object`是所有类型的超类，由于泛型的不可协变性，**它只能表示`List`中可以容纳所有类型的对象，却不能表示任何参数类型的`List<E>`。**

而`List<?>`则是通配符类型中的一种特例，它并没有`extend`或`super`这样的限制，从而可以做到引用任意参数类型的`List<E>`。但由于没有表示类型的符号（`E`），在方法中无法引用这个类型，所以它只用于无需使用具体类型的方法之中，如果不是这个情况，则需要使用泛型方法（只用`List<?>`的**不是**一个泛型方法，它具有`List<?>`这个固定的参数`）。

但是`List<?>`还是不能用作上面的`unsafeAdd`的参数，修改后会出现一条奇怪的编译错误：

    #!shell
    error: no suitable method found for add(Object)
            list.add(object);
            ^
    method Collection.add(CAP#1) is not applicable
      (argument mismatch; Object cannot be converted to CAP#1)
    method List.add(CAP#1) is not applicable
      (argument mismatch; Object cannot be converted to CAP#1)
    where CAP#1 is a fresh type-variable:
        CAP#1 extends Object from capture of ?

这是因为无法将任何元素（`null`除外）放入`List<?>`中。这又是为什么呢？先来看一个有限定通配符的例子：

    #!java
    public class DiffInGeneric {
        public static void main(String[] args) {
            List<? extends Number> numbers = new ArrayList<Integer>();
            numbers= new ArrayList<Double>();
            numbers= new ArrayList<Float>();
            numbers = new ArrayList<Number>();
            numbers.add(new Integer(1));
        }
    }

第7行报出了与之前相似的编译错误：

    #!shell
    error: no suitable method found for add(Integer)
        numbers.add(new Integer(1));
               ^
    method Collection.add(CAP#1) is not applicable
      (argument mismatch; Integer cannot be converted to CAP#1)
    method List.add(CAP#1) is not applicable
      (argument mismatch; Integer cannot be converted to CAP#1)
    where CAP#1 is a fresh type-variable:
        CAP#1 extends Number from capture of ? extends Number

这次我们可以看出错误的原因：可以将一个`List<Integer>`传递给`List<? extends Number>`，因为`Integer`是`Number`的子类，符合限定符的条件。同理，也可以将类似的对象传递给它，当然也可以把`List<Number>`传递给它。

如果允许这个对象的`add`操作，我们无法知道这个参数是否与对象的泛型参数相同，因为我们只知道它是`Number`的一个子类。

    #!java
    List<? extends Parent> list = new ArrayList<Child>();
    List<? extends Parent> parents = list;
    list.add(new Parent());

上面的1,2两行是完全合法的，如果允许第3行的`add`操作，那么会把一个`Parent`对象加入到一个实际类型是`Child`的`List`中，而`Parent`is-not-a `Child`，这破坏了Java的类型安全，是绝对不允许的。

上面是有限制通配符的情况，那么针对`List<?>`这样的无限制通配符更是如此。因此，为了保证类型安全，不允许对`List<?>`或`List<? extends E>`这样的通配符类型进行类似`add`的操作。

使用泛型方法可以避免这个问题（重申通配符类型并不是泛型方法），使用无限制通配符类型可以取代其他需要表示**包含某一种对象类型的泛型类型**的情况而不是使用原生态类型`List`。