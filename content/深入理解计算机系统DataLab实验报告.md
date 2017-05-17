Title: 深入理解计算机系统DataLab实验报告
Date: 2017-04-04 16:50:20
Category: 计算机系统
Tags: 计算机系统, 实验
Authors: Zhihao Chen

实验答案托管在我的[GitHub](https://github.com/BlackDragonF/CSAPPLabs/tree/master/DataLab)上

> 总共花了五天时间完成了《深入理解计算机系统》(Computer Science A Programmer's Perspective)的第一个Lab - Data Lab，深感这次实验的效率低下。一方面是由于清明假期自己有所惰怠，另一方面也是由于在做题的时候采取了不正确的方法，在已经明知不会的情况下我还继续投入大量无意义的时间，没有取得很好的学习效果。

## 实验简介

Data Lab - Manipulating Bits主要是关于位操作的实验，对应于书本的第2章：信息的表示和处理。

在该实验中，学生主要需要在一个严格限制的C子集（使用优先的位运算符以及顺序结构的代码）中实现简单的逻辑，补码以及浮点数相关的函数。本实验的目的是为了让学生熟悉整数和浮点数的位级表示。

本实验的核心在于在各种受限制的条件下完成给出的15个谜题。其中包括5个位操作的谜题，7个补码运算的谜题，以及3个浮点数操作的谜题。其中每完成一个谜题都能得到一定的分数，如果使用的运算符数目小于给定的数目，还能获得加分。本实验的满分是71分。可以通过讲义中的driver.pl脚本直接计算出总分数。

关于本实验具体的介绍详见[实验讲义](http://csapp.cs.cmu.edu/3e/datalab-handout.tar)。

## 测试程序btest make失败及解决办法

在完成实验的功能中需要用到`make && ./btest`命令进行答案正确性的检查，结果系统返回了`fetal error: gnu/stubs-32.h:No such file or directory`。

经过检查发现是系统是Archlinux 64位，而Makefile中包含了-m32的编译参数导致的。

通过启用multilib仓库使得可以在64位的ArchLinux系统上编译和运行32位的程序，问题得以解决。

编辑/etc/pacman.conf，取消下面内容的注释：

{% codeblock lang:vim %}
[multilib]
include = /etc/pacman.d/mirrorlist
{% endcodeblock %}

更新软件包列表并升级系统`pacman -Syu`

然后安装gcc-multilib并重新执行`make && ./btest`，问题解决。

## 实验限制

### 整数代码规则

整数代码应遵循如下的基本结构：
{% codeblock lang:c %}
int Funct(arg1, arg2, ...) {
    /* brief description of how your implementation works */
    int var1 = Expr1;
    ...
    int varM = ExprM;
    varJ = ExprJ;
    ...
    varN = ExprN;
    return ExprR;
}
{% endcodeblock %}

每一个表达式只能使用：
1. 0～255之间的常量（包括0和255）
2. 函数的参数和局部变量
3. 单目运算符 ! ~
4. 双目运算符 & ^ | + << >>

注意，部分题目对于运算符有着更加严格的限制，但是你可以在一行代码中使用多个运算符。

你将会被禁止：
1. 使用任何的分支或者循环结构
2. 定义或者使用任何的宏
3. 在文件中定义任何额外函数
4. 调用任何函数
5. 使用任何其他的运算符
6. 使用任何形式的类型转换
7. 使用除了int意外的其他数据类型，这意味着你不能使用数组，结构或联合

你可以假设你的机器：
1. 使用32位补码表示整数
2. 使用算术右移
3. 对整数进行的位移运算的位数超越了字长是未定义的行为

### 浮点代码规则

浮点运算的规则相对较为宽松，你可以使用循环或者是分支结构，你被允许同时使用int和unsigned，此外，你还可以使用任意的常量。

你将会被禁止：
1. 定义或者使用任何的宏
2. 在文件中定义任何额外函数
3. 调用任何函数
4. 使用任何形式的类型转换
5. 使用除了int和unsigned以外的任何数据类型，这意味着你不能使用数组，结构或者联合
6. 使用任何浮点数的数据类型，操作或者是常量

## 实验答案及分析

### 第一部分 位操作

* bitAnd
    问题：要求使用~和|以及不超过8个操作符实现x&y
    分析：使用De Morgan定律即可
    答案：
    {% codeblock lang:c %}
    int bitAnd(int x, int y) {
    /* x&y = ~(~(x&y)) = ~(~x|~y) */
    	return ~(~x | ~y);
    }
    {% endcodeblock %}

* getByte
    问题：要求使用! ~ & ^ | + << >>以及不超过6个操作符返回x中的第n个字节(0(LSB)<=n<=3(MSB))。
    分析：根据不同的n值将x右移不同的位数，然后使用掩码0xFF取得最低位数的字节即可。先左移再右移会导致算术右移，需要小心。
    答案：
    {% codeblock lang:c %}
    int getByte(int x, int n) {
    /* right shift in order to avoid boring arithmatic shift and try to get specific byte using bitAnd and mask. */
        return ((x >> (n << 3)) & 0xFF);		
    }
    {% endcodeblock %}

* logicalShift
    问题：要求使用! ~ & ^ | + << >>以及不超过20个操作符实现将int值x的逻辑右移n位。
    分析：通过将一个全1的数通过算术右移的方式构造掩码，然后与算术右移的掩码求按位与即可。
    注意，直接右移32位的结果是未定义的，需要额外处理这种情况。
    答案：
    {% codeblock lang:c %}
    int logicalShift(int x, int n) {
    /* try to implement logical right shift by mask and logical right shift */
        int mask = ((~0) << (31 + (~n + 1))) << 1;
        return (x >> n) & (~mask);
    }
    {% endcodeblock %}

* bitCount
     问题：要求使用! ~ & ^ | + << >>以及不超过40个操作符计算一个数字x中有多少为1的位。
     分析：
     本题参考[stackoverflow](http://stackoverflow.com/questions/3815165/how-to-implement-bitcount-using-only-bitwise-operators)上的回答，并结合题目要求做了一些改动。
     核心的思想是分治法，通过将原数字x中的位按每1,2,4...个位分组，按相邻组进行累加，最后求出结果。
     举例来说，假如现在有一个数395，它的二进制表示是0000000110001011(16位)，首先我们将这个数按1位分组，得到：
     0 0 0 0 0 0 0 1 1 0 0 0 1 0 1 1
     然后我们将相邻的组累加，得到：
     0+0 0+0 0+0 0+1 1+0 0+0 1+0 1+1
     00 00 00 01 01 00 01 10
     然后我们继续将相邻的组累加，得到：
     00+00 00+01 01+00 01+10
     0000 0001 0001 0011
     然后我们继续将相邻的组累加，得到：
     0000+0001 0001+0011
     00000001 00000100
     最后，我们最后的两个组累加，得到：
     00000001+0000100=00000101
     结果是5，为正确答案。
     答案：
     {% codeblock lang:c %}
     int bitCount(int x) {
    /* Divide and Conquer */
        int mask = 0x55 + (0x55 << 8) + (0x55 << 16) + (0x55 << 24);
        x = (x & mask) + ((x >> 1) & mask);
        mask = 0x33 + (0x33 << 8) + (0x33 << 16) + (0x33 << 24);
        x = (x & mask) + ((x >> 2) & mask);
        mask = 0xF + (0xF << 8) + (0xF << 16) + (0xF << 24);
        x = (x & mask) + ((x >> 4) & mask);
        return (x + (x >> 8) + (x >> 16) + (x >> 24)) & 0xFF;
    }
    {% endcodeblock %}

* bang
    问题：要求使用~ & ^ | + << >>以及不超过12个操作数计算x的逻辑非。
    分析：
    逻辑非要求将0变成1，将非0的数变成0。生成0或1可以通过与掩码0x1求按位与实现，重点在于如何构造一个表达式使得0和非0的数产生不同的结果。
    可以考虑对于任意一个非0的数，它的负数都是从最高位到其最低位的1为止(不包括最低位的1)全部取反的结果。
    例如，14是00001110(8位)，而-14是11110010(8位)，为14从最高位到最低位的1(不包括这个1)，也就是000011取反，而最低位的10不变的结果。
    而0的负数永远是0。
    从这里我们可以看出，对于一个非0的数，它与它的负数按位或的结果的最高位一定会是1，而0与非0的按位或的结果的最高位永远是0。我们可以以此实现逻辑非。
    答案：
    {% codeblock lang:c %}
    int bang(int x) {
    /* for x != 0, the highest bit of x | (-x) will always become 1 while when x == 0, the result is the opposite */
    	return (~((x | (~x + 1)) >> 31) & 1);
    }
    {% endcodeblock %}

### 第二部分 补码运算

* tmin
    问题：要求使用! ~ & ^ | + << >>以及不超过4个运算符返回以补码表示的最小的整数。
    分析：根据补码到整数的公式，最小的整数的补码表示为10000...
    答案：
    {% codeblock lang:c %}
    int tmin(void) {
        /* TMin = 10000.... */
        return (1 << 31);
    }
    {% endcodeblock %}

* fitsBits
    问题：要求使用! ~ & ^ | + << >>以及不超过15个操作符判断x是否能表示成n位的补码，如果是，则返回1，反之则返回0。
    分析：
    这个问题需要分正数和负数两种情况讨论，对于正数来说，如果一个数x能表示成n位的补码，那么它从最高位直到第n位一定全部为0，它的第n位一定不能为1，否则它就会变成一个负数。对于一个负数来说，如果一个数x能表示成n位的补码，那么它只需从最高位到第n位全部为1即可。
    因此，我们可以先将x右移n-1位，对于满足条件的正数和负数，这将产生一个全0的数或是一个全1的数。然后我们可以根据x的符号构造一个全0或者是全1的掩码。通过将这两个数按位异或并且取逻辑非，就能得到正确的结果。
    答案：
    {% codeblock lang:c %}
    int fitsBits(int x, int n) {
    /* if fitsBits then from highest bit to n bit will all become 1 - negative number or 0 - positive number
     * then can construct a mask to implement fitsBits with the help of ^ and !
     */
        return !((x >> (n + (~1) + 1)) ^ (((1 << 31) & x) >> 31));
    }
    {% endcodeblock %}

* divpwr2
    问题：要求使用! ~ & ^ | + << >>以及不超过15个操作符求出x/(2^n)的结果，其中0<=n<=30。
    分析：对于正数，直接使用算术右移即可；对于负数，需要加上适当的偏移量以实现向上舍入，这可以用根据符号位生成1个全0或者全1的掩码来控制。
    答案：
    {% codeblock lang:c %}
    int divpwr2(int x, int n) {
    /* add bias when x is negative, which is controlled by a sign-related mask */
    	int mask = x >> 31;
    	int add = ((1 << n) + (~1) + 1) & mask;
    	return (x + add) >> n;
    }
    {% endcodeblock %}

* negate
    问题：要求使用! ~ & ^ | + << >>以及不超过5个操作符求出x的负数。
    分析：-x = (~x + 1)
    答案：
    {% codeblock lang:c %}
    int isPositive(int x) {
    ／* -x = (~x) + 1 *／
    	return (!(x >> 31)) ^ (!(x ^ 0));
    }
    {% endcodeblock %}

* isPositive
    问题：要求使用! ~ & ^ | + << >>以及不超过8个操作符判断x是否为正数。
    分析：对于正数，它的最高位一定是0，同时还要排除0的影响。
    答案：
    {% codeblock lang:c %}
    int isPositive(int x) {
    /* ensure the highest bit is 0 and x != 0 */
    	return (!(x >> 31)) ^ (!(x ^ 0));
    }
    {% endcodeblock %}

* isLessOrEqual
    问题：要求使用! ~ & ^ | + << >>以及不超过24个操作符判断x是否小于或等于y。
    分析：
    对于这个问题，我们需要按照是否溢出，以及x与y的符号分别讨论。
    最基本的思路是，做y-x，若结果的符号位为1，则返回0，反之返回1。但这样就忽略了溢出可能导致的问题，现在我们做如下考虑。
    若x，y均为正数，或x，y均为负数，则y-x绝不可能溢出，因此可直接用差的符号位判断大小。
    若x为正数，y为负数，可以直接返回0。
    若x为负数，y为正数，可以直接返回1。
    我们可以生成两种条件变量，一种为x，y同号时返回正确结果的条件变量，另一种为x，y异号时返回正确结果的条件变量。
    对于x，y同号和异号这两种不同的情况，我们可以用!((x ^ y) >> 31)生成掩码使得在任意的情况下，只有正确的条件变量生效。
    答案：
    {% codeblock lang:c %}
    int isLessOrEqual(int x, int y) {
    /* different processing ways when x and y have the same signs or different signs */
    	int diff = y + (~x) + 1;
    	int not_diff_sign = !(diff >> 31);
    	int mask = !((x ^ y) >> 31);
    	int result_not_overflow = mask & not_diff_sign;
    	int result_overflow = (!mask) & (x >> 31);
    	return result_overflow | result_not_overflow;
    }
    {% endcodeblock %}


* ilog2
    问题：要求使用! ~ & ^ | + << >>以及不超过90个操作数求出x以2为底的对数（向下舍入），保证x>0。
    分析：
    这道题参考了网上的答案。核心的思想是二分查找。
    首先将x右移16位，如果x>0，则表明结果的第5位为1，将该位置为1。
    然后根据结果将x右移8位（第5位为0）或者将x右移24位（第5位为1），如果x>0，则表明结果的第4位为1，将该位置为1。
    以此类推，直到得出结果。
    答案：
    {% codeblock lang:c %}
    int ilog2(int x) {
    	/* Binary Search */
    	int result = (!!(x >> 16) << 4);
    	result = result + ((!!(x >> (result + 8))) << 3);
    	result = result + ((!!(x >> (result + 4))) << 2);
    	result = result + ((!!(x >> (result + 2))) << 1);
    	result = result + (!!(x >> (result + 1)));
    	return result;
    }
    {% endcodeblock %}

### 第三部分 浮点数操作

* float_neg
    问题：返回对于浮点数参数f，-f的等价的位级表示。当参数位NAN时，返回NAN。函数的参数和返回值均为unsigned，但它们实际上都是浮点数的位表示。最多允许使用10个操作符。
    分析：首先要判断参数是否是NAN，如果是则直接返回，否的话直接将参数的最高位取反即可。
    NAN的阶码全为1，尾码不全为0。
    答案：
    {% codeblock lang:c %}
    unsigned float_neg(unsigned uf) {
    /* m_flag - if m != 0 e_flag - if e == 0xff */
    	unsigned m_flag = 0x007fffff & uf;
    	unsigned e_flag = !(0x7f800000 & (~uf));
    	if (e_flag && m_flag) {
    		return uf;
    	} else {
    		return 0x80000000 ^ uf;
    	}
    }
    {% endcodeblock %}

* float_i2f
    问题：返回(float)x的位级的等价表示。结果被作为unsigned int返回，但它实际上是单精度浮点数的位表示。最多允许使用30个操作符。
    分析：
    首先考虑到整数中只有0会被转换为非规格化浮点数，而其他整数会被转化为规格化浮点数。因此对于0需要做额外的处理。
    其次，对于负数，我们需要将其转化为正数再做处理，这就要求我们需要将x的符号保存下来，并且从补码转化为无符号表示。
    然后，我们需要根据转换成无符号数的x算出阶码e和尾码m。
    最后，我们将尾码舍入后再和阶码符号一起，生成最终的结果即可。
    这里我有一个比较大的误区，舍入的时候看的不仅仅是带舍入位的下一位，而是待舍入位之后的所有位。
    答案：
    {% codeblock lang:c %}
    unsigned float_i2f(int x) {
    /* 1.process 0 individually 2.process negative number and store the sign 3.get the e number 4.get the m number and round it 5.construct the result */
    	unsigned count = 0;
    	unsigned mask = 0x80000000;
    	unsigned sign = x & mask;
    	unsigned c = 0, absx = x;
    	if (x == 0) {
    		return 0;
    	} else {
    		if (x < 0) {
    			absx = -x;
    		}
    		while (!(mask & absx)) {
    			count = count + 1;
    			mask = mask >> 1;
    		}
    		absx = absx << (count + 1);
    		if (((absx & 0x1ff) > 0x100) || ((absx & 0x3ff) >= 0x300)) {
    			c = 1;
    		}
    		return sign + ((158 - count) << 23) + (absx >> 9)+ c;
    	}
    }
    {% endcodeblock %}

* float_twice
    问题：返回对于浮点数参数f，2*f的等价的位级表示。参数和结果都为unsigned int，但它们实际上是浮点数的位表示。当参数是NAN时，返回NAN。最多允许使用30个操作符。
    分析：
    对于非规格化浮点数，只要在保留符号位的情况下将尾码m右移一位即可，这样同时解决了尾码乘以二和进位的情况。
    对于规格化浮点数，只要将其阶码e加1即可。
    答案：
    {% codeblock lang:c %}
    unsigned float_twice(unsigned uf) {
    /* denormailized number - m = m << 1 normalized number - e = e + 1 */
    	unsigned result = uf;
    	if ((uf & 0x7f800000) == 0) {
    		result = ((uf & 0x007fffff) << 1) | (uf & 0x80000000);
    	} else if ((uf & 0x7f800000) != 0x7f800000) {
    		result = uf + 0x00800000;
    	}
    	return result;
    }
    {% endcodeblock %}
