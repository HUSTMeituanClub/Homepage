Title: 神威·太湖之光初体验
Date: 2017/4/6 16:05:24
Categories: supercomputer
Tags: Contest, Parallelization
Authors: Yifeng Tang


# 神威·太湖之光初体验

    在ASC17的比赛中，本菜鸡负责了MASNUM这样一个从上世纪90年代就开始发展的海浪模拟应用的在神威·太湖之光上的优化任务（虽然最后并没能在要求时间内跑完最后一个workload。。账号一开始被赛委会删了可能也是一个原因（？！！）。。），并且借此机会也尝试了一下神威的速度，同时踩了上面的许许多多的坑。

## 神威的结构

![神威的结构图](/images/2017_4_30_1.png)

神威采用的是完全国产的SW26010处理器，其中每一个处理器有四个核组（CGs),这些核组之间是通过一个芯片上的网络互相连接的。每一个CG包含了一个内存管理器（MC）、消息处理核心（MPE）、计算处理核心集群（CPEs)。其中MPE支持完整的中断功能，内存管理，超标量和乱序问题/执行，擅长处理管理，任务进度和数据通信，而CPEs旨在最大限度地提高聚合计算吞吐量，同时最小化微架构的复杂性。相对于MPE，CPE不支持中断。

<!--more-->

其中MPE主频为1.45GHz，每一个核组内存8GB，L1缓存32KB，L2缓存256KB，核组之间的一般通过MPI进行通讯。从核主频为1.45GHz，每一个从核分别有64KB的局部存储空间，从核可以通过gld／gst离散访问或者DMA批量访问主寸，从核阵列之间可以通过寄存器通信进行低延迟的通信。有意思的是，CPE的LDM在栈空间很大时，可能会使得栈空间、局存、动态分配的空间相互冲突，如下图所示。如果想要发生冲突的时候报错，需要加入-preserve preserve_size编译命令。

![LDM的使用情况](/images/2017_4_30_2.png)

## MASNUM的优化思路

由于在去年的SC大会上，一篇关于在神威上对MASNUM的优化的论文成功进入了Gorden Bell Prize的提名，所以几乎所有的队伍都是在做着成功实现论文的工作。

[A highly effective global surface wave numerical simulation with ultra-high resolution. 46-56](http://dblp2.uni-trier.de/db/conf/sc/sc2016.html)

论文上实现了三部分的优化，不过就算是做得最好的清华似乎也只是实现了其中的第二部分，简单点说就是把所有的运算全部扔到CPEs中进行并行计算，而我们也是在试图实现第二部分的优化。

经过分析可以发现其中有两个子程序implsch、propagat是整个程序的热点（最后交卷的时候只让填这两个子程序的运行时间也能看出来这点）。其中implsch是很容易优化的，因为implsch使用的所有数组数据都并没有超出循环变量的范围，通过分组映射发射之类的办法很容易就能把相应数据填入CPEs之中，从而榨干CPE的所有局部内存。然而propagat我们到最后也没能实现，因为其中有一个数据规模随着输入平方级增加的四位数组在程序上表现为是乱序使用数据的，在程序运行之前是无法预测可能需要哪一个数据的。。最后试着每次循环都离散读取这8个变量，反而运行时间提升了4倍。。从清华他们那里打听了消息，原来这8个变量就是一个九宫格中间那一个点附近周围的8个，但是我们只是一开始猜想了一下并没有仔细推论。。（同队的大佬一开始就说可能是在计算微分方程，但我和另一个哥们都没能引起重视继续向下思考，毕竟这程序写得就像那一坨那啥）

## 神威上的加速库（Fortran下的）

    神威上的加速库的目标差不多，就是将程序划分为host、slave两块，然后让MPE运行host的内存，CPE运行slave的内容。从编译器必须加 -host 、 -slave 或者 -hybrid 也能看出来这一点。

### Open-ACC*

神威上的Open-ACC*是在Open-ACC 2.0的基础上进行魔改之后的东西。虽然我们和清华交流的时候统一了这东西不知道有什么意义、只会越跑越慢的意见，但是本菜鸡自己还是觉得可能是我们的打开方式都有点不对，不过现在也没办法试验，只能把其中遇见的问题再留在这里。

1. 似乎没能够将数组很好地分块

    对于一个四维数组例如e(a, b, c, d)，如果关键循环变量是a，b的话，Open-ACC*似乎没有办法能够将a，b下的其他两个维度的数据拿出来，就算能够拿出来也似乎没有办法将在a，b两个维度上进行分段批量读取。（至少文档上完全没提到）

2. 似乎只能把数组按照循环变量进行分块

    但有一些例如propagat这样需要获取附近的8个点的数据的操作，Open-ACC*可能很难实现。

3. 文档上的很多看似很简单的功能实际上极难实现

    反正菜鸡我照着这个文档做，基本都是在无限报错。

4. 加速区只能是循环，且不允许两个加速区的并列

    这一点就真的有点烦躁，有些时候你将会需要一些例如一部分CPE进行读取、一部分CPE进行转发、一部分CPE进行计算这样的复杂功能，然后就会发现Open-ACC*就不能执行这样的复杂操作。

综上所述，我建议如果你的程序是对数组读取非常简单，或者是数组很小，并且不需要让每一个CPE分别有自己特殊的职责的话，可以选择使用Open-ACC*来进行优化。

菜鸡我一开始就是使用Open-ACC*来进行的优化，优化的最好效果是让时间翻倍。。。（不过还是有队伍使用Open-ACC成功进行了优化，我确实很好奇到底是怎样完成的。。或许从一开始就已经分出了胜负）

### Athread

    神威上的Athread的文档全是用C来写的，然而MASNUM却是一个Fortran写的程序，我们一开始以为应该C有的API、Fortran也应该都有，然而真相是非常的残酷。所以以后一定要把全部代码用C重写一次，否则会感到非常绝望。（至少要混合编译将C的API给包装过来）

Athread是一个相对于Open-ACC*来说更加靠谱的库，它的功能更加复杂且强大，不过我们也只是用了最基础的几个操作就完成了对implsch的优化，并且使得它的运行速度提高了100倍（从15000s的运行时间到了150s）。在这里就大致介绍一下关键的函数或者说子程序。

#### host部分

1. athread_init()

    启动整个加速线程库，可以选择在程序最开始就初始化。说不定有什么性能的影响，菜鸡我也没办法再试验了。

2. athread_spawn(fun, address)

    创建线程组，其中第一个参数是相应slave程序的函数，一般会写到另一个文件然后用external来调用，第二个参数是参数的起始地址。可以感觉到如果有多个参数将会非常的不方便，所以就用全局变量进行传递其实更好一些，具体效率在下也没测试。

3. athread_join()

    阻塞等待线程组的全部结束。这个函数可以在MPE经过其他运算之后再调用，这样就实现了更进一步的并行。

4. athread_halt()

    将整个加速线程库全部关闭，可以丢在程序最后面去。

#### slave部分

slave文件中是通过/Common/区来进行对主存的直接访问，其中动态数组只能全部改成pointer然后来进行共享。然而CPEs内部的共享在下没能找到对应的API以及方法，提供的Openmp预编译指令也没能按照文档上所写的实现它的功能。。希望下一次能够找到方法。

1. get_myid()

    这个最关键的获取cpe自己的逻辑顺序的API在Fortran里面其实是没有的。。。赛委会给我们现场拷来了C语言的实现，然后混合编译进行调用。。真有意思。。（源代码我就不上传了，还是有点虚）

2. athread_get(0, src, des, len, reply, 0, 0, 0)

    这几个0其实都有自己的意义，但是我们一般都不会用到。。想仔细用查查文档吧，可能会有进一步的提升。src是指经过common区共享的主内存的数据，des是指LDM中对应的数据位置，len是以字节计算的长度，reply是一个计数变量，会在get成功之后自增1。例程上面使用了简单的do while来进行等待，但是实际操作时，神威的工程师告诉我们，编译器可能会优化掉do while里面的reply从而使得整个程序卡住。所以尽量将do while写到另一个文件里面然后编译这个文件时加上-O0或者是-g（神威里面的-g默认-O0），从而避免这个优化。

3. athread_put(0, src, des, len, reply, 0, 0)

    除了des与src是反着的，其他基本同上。

4. ldm_malloc

    不好意思，Fortran里面没有，不过也可以完全避免动态数组的出现。

## 具体并行思路

由于程序就是循环构成的，并行思路也比较简单，大致如下：

1. 先估算每一个点所需要的内存大小；

2. 用64kb除以估算的内存大小，就可以得到最多能够一次存下的点的数量；

3. 通过总点数/(点的数量*64)，就可以得到想要把所有数据全部计算所需要的大的循环的次数；

4. 每一次批量读取数据进行计算再批量取出即可;

5. 某些变量以及固定长度的数组每一个CPE在一开始一起读入即可。

具体关键映射操作如下Java代码所示（Fortran数组是从1开始计算的）

其中ixs、ixl、iys、iyl是点的范围，max_cpe_size是估算的最大点数，how_many是最大能够平均分配的循环次数，left_part是余下数量。

计算之后steps是当前需要计算的长度，简单的从1到steps循环即可。

```java
public class Test {

    public static void main(String[] args) {
        int ixl = 10000, iyl = 10;
        int ixs = 1, iys = 1;
        int max_cpe_size = 350;
        int how_many = (iyl - iys + 1) * (ixl - ixs + 1) / (max_cpe_size * 64);
        int left_part = (iyl - iys + 1) * (ixl - ixs + 1) - how_many * max_cpe_size * 64;
        int steps = 0, ia = 0, ic = 0, my_id, step_base, step_left;

        for (int big_loop = 1; big_loop <= how_many + 1; big_loop++) {
            for (my_id = 1; my_id <= 64; my_id++) {
                if (big_loop != how_many + 1) {
                    steps = max_cpe_size;
                    ic = (((big_loop - 1) * max_cpe_size * 64) + (my_id - 1) * max_cpe_size) / (ixl - ixs + 1);
                    ia = (((big_loop - 1) * max_cpe_size * 64) + (my_id - 1) * max_cpe_size) - ic * (ixl - ixs + 1);
                } else {
                    step_base = left_part / 64;
                    step_left = left_part - step_base * 64;
                    if (my_id <= step_left) {
                        steps = step_base + 1;
                        ic = ((how_many * max_cpe_size * 64) + (my_id - 1) * steps) / (ixl - ixs + 1);
                        ia = ((how_many * max_cpe_size * 64) + (my_id - 1) * steps) - ic * (ixl - ixs + 1);
                    } else {
                        steps = step_base;
                        ic = ((how_many * max_cpe_size * 64) + (step_left) * (step_base + 1) + (my_id - step_left - 1) * steps) / (ixl - ixs + 1);
                        ia = ((how_many * max_cpe_size * 64) + (step_left) * (step_base + 1) + (my_id - step_left - 1) * steps) - ic * (ixl - ixs + 1);
                    }
                }
                ic = ic + 1;
                ia = ia + 1;
            }
        }
    }
}
```

## 出错整理

神威的Exception非常的不详细，甚至他们的工程师自己都在吐槽，不过本菜鸡经过认真的测试，大致发现了以下的对应的规律。

1. No SPE Exception

    可能是栈空间不足。

2. Floating Pointer Exception

    可能是程序计算映射出错，导致内存溢出到非法区域。

3. DMA Desxxxxxxxx? Exception

    可能是循环的时候未处理steps = 0的情况。

4. Unknown Exception

    呃。。别问我发生了什么

5. 程序在athread_get卡住

    检查-cgsp -b参数，或者-O0参数进行测试

## 资料出处

[无锡国家计算中心官网](http://www.nsccwx.cn)

## 优化后实例代码

源文件：

```fortran
!-------------------------------------------------------------------------------
!@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
!-------------------------------------------------------------------------------
!*DeckYinxq: mean2
 ! �����׾أ����ڼ���Դ����

  subroutine mean2

  implicit none

!-------------------------------------------------------------------------------

  integer :: k, k1, i, i1, j
  real :: dwkk, wfk, wfk1, wsk, wsk1, wkk, wkk1, ekj, ekj1

!-------------------------------------------------------------------------------

  do 100 ic=iys,iyl
  do 100 ia=ixs,ixl

    ae(ia,ic)=0.
    asi(ia,ic)=0.
    awf(ia,ic)=0.
    awk(ia,ic)=0.
    ark(ia,ic)=0.

    if(nsp(ia,ic).ne.1) cycle

    do 200 k=1,kld
      k1=k+1
      i=k-kl+1
      i1=i+1
      dwkk=dwk(k)
      wfk=wf(k,ia,ic)
      wfk1=wf(k1,ia,ic)
      !      wfk=fr(k)
      !      wfk1=fr(k1)
      wsk=zpi*wfk
      wsk1=zpi*wfk1
      wkk=wk(k)
      wkk1=wk(k1)
      do 200 j=1,jl
        if (k.lt.kl) then
          ekj=e(k,j,ia,ic)
          ekj1=e(k1,j,ia,ic)
        else
          ekj=e(kl,j,ia,ic)*wkh(i)
          ekj1=e(kl,j,ia,ic)*wkh(i1)
        endif
        ae(ia,ic)=ae(ia,ic)+(ekj+ekj1)*dwkk
        awf(ia,ic)=awf(ia,ic)+(ekj*wfk+ekj1*wfk1)*dwkk
        asi(ia,ic)=asi(ia,ic)+(ekj/wsk+ekj1/wsk1)*dwkk
        awk(ia,ic)=awk(ia,ic)+(ekj*wkk+ekj1*wkk1)*dwkk
        ark(ia,ic)=ark(ia,ic)+(ekj/sqrt(wkk)+ekj1/sqrt(wkk1))*dwkk
    200      continue

    asi(ia,ic)=ae(ia,ic)/asi(ia,ic)
    awf(ia,ic)=awf(ia,ic)/ae(ia,ic)
    awk(ia,ic)=awk(ia,ic)/ae(ia,ic)
    ark(ia,ic)=(ae(ia,ic)/ark(ia,ic))**2

  100      continue

!-------------------------------------------------------------------------------

  return

!-------------------------------------------------------------------------------

  end subroutine mean2

!-------------------------------------------------------------------------------
!@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
!-------------------------------------------------------------------------------

```

host代码：

```fortran
subroutine mean2

    implicit none

    integer :: how_many, left_part

    integer,external::slave_mean2_slave

    integer, parameter :: max_cpe_size = 35

    common /mean2_host_hm/ how_many
    common /mean2_host_lp/ left_part

    how_many = (iyl - iys + 1) * (ixl - ixs + 1) / (max_cpe_size * 64)
    left_part = (iyl - iys + 1) * (ixl - ixs + 1) - how_many * max_cpe_size * 64

    call athread_spawn(slave_mean2_slave, 1)
    call athread_join()

  return

end subroutine mean2
```

slave代码:

```fortran
subroutine mean2_slave

    implicit none

    integer :: my_id, reply, fak

    integer :: how_many, left_part
    integer :: big_loop, steps, step_left, step_base

    integer :: k, k1, i, i1, j, ia, ic
    integer :: count
    real :: dwkk, wfk, wfk1, wsk, wsk1, wkk, wkk1, ekj, ekj1

    integer, parameter :: kld = 30
    integer, parameter :: kl = 25
    integer, parameter :: jl = 12
    integer, parameter :: zpi = 3.1415926 * 2

    integer, parameter :: max_cpe_size = 35

    integer :: iys, iyl, ixs, ixl
    real, pointer :: ae(:,:), asi(:,:), awf(:,:), awk(:,:), ark(:,:), nsp(:,:)
    real, pointer :: wf(:, :, :)
    real, pointer :: e(:, :, :, :)
    real :: dwk(31), wk(31), wkh(31)

    integer :: how_many_slave, left_part_slave

    integer :: iys_slave, iyl_slave, ixs_slave, ixl_slave
    real :: dwk_slave(31), wk_slave(31), wkh_slave(31)
    real :: ae_slave(35), asi_slave(35), awf_slave(35), awk_slave(35), ark_slave(35), nsp_slave(35)
    real :: wf_slave(35 * 31), e_slave(35 * 25 * 12)

    integer,external::get_myid

    common /mean2_host_hm/ how_many
    common /mean2_host_lp/ left_part

    common /sh_iys/ iys
    common /sh_iyl/ iyl
    common /sh_ixs/ ixs
    common /sh_ixl/ ixl

    common /sh_ae/ ae
    common /sh_asi/ asi
    common /sh_awf/ awf
    common /sh_awk/ awk
    common /sh_ark/ ark
    common /sh_nsp/ nsp
    common /sh_wf/ wf
    common /sh_e/ e

    common /sh_dwk/ dwk
    common /sh_wk/ wk
    common /sh_wkh/ wkh

    fak = get_myid(my_id)

    how_many_slave=how_many
    left_part_slave=left_part

    iys_slave=iys
    ixs_slave=ixs
    iyl_slave=iyl
    ixl_slave=ixl

    reply = 0
    call athread_get(0, dwk(1), dwk_slave(1), 4 * 31, reply, 0, 0,0)
    call athread_get(0, wk(1), wk_slave(1), 4 * 31, reply, 0, 0,0)
    call athread_get(0, wkh(1), wkh_slave(1), 4 * 31, reply, 0, 0,0)
    do while(reply .ne. 3)
    end do

    do 9999 big_loop = 1, how_many_slave + 1

        if (big_loop .ne. how_many_slave + 1) then
            steps = max_cpe_size
            ic = (((big_loop - 1) * max_cpe_size * 64) + (my_id - 1) * max_cpe_size) / (ixl_slave - ixs_slave + 1)
            ia = (((big_loop - 1) * max_cpe_size * 64) + (my_id - 1) * max_cpe_size) - ic * (ixl_slave - ixs_slave + 1)
            ic = ic + 1
            ia = ia + 1
        else
            step_base = left_part / 64   !34
            step_left = left_part - step_base * 64   !56
            if (my_id .le. step_left) then
                steps = step_base + 1
                ic = ((how_many_slave * max_cpe_size * 64) + (my_id - 1) * steps) / (ixl_slave - ixs_slave + 1)
                ia = ((how_many_slave * max_cpe_size * 64) + (my_id - 1) * steps) - ic * (ixl_slave - ixs_slave + 1)
            else
                steps = step_base
                ic = ((how_many_slave * max_cpe_size * 64) + (step_left) * (step_base + 1) + (my_id - step_left - 1) * steps) / (ixl_slave - ixs_slave + 1)
                ia = ((how_many_slave * max_cpe_size * 64) + (step_left) * (step_base + 1) + (my_id - step_left - 1) * steps) - ic * (ixl_slave - ixs_slave + 1)
            endif
            ic = ic + 1
            ia = ia + 1
        endif

        reply = 0

        call athread_get(0, ae(ia, ic), ae_slave(1), 4 * steps, reply, 0, 0,0)
        call athread_get(0, asi(ia, ic), asi_slave(1),  4 * steps, reply, 0, 0,0)
        call athread_get(0, awf(ia, ic), awf_slave(1), 4 * steps, reply, 0, 0,0)
        call athread_get(0, awk(ia, ic), awk_slave(1), 4 * steps, reply, 0, 0,0)
        call athread_get(0, ark(ia, ic), ark_slave(1), 4 * steps, reply, 0, 0,0)
        call athread_get(0, nsp(ia, ic), nsp_slave(1),  4 * steps, reply, 0, 0,0)

        call athread_get(0, wf(1, ia, ic), wf_slave(1), 4 * 31 * steps, reply, 0, 0,0)
        call athread_get(0, e(1, 1, ia, ic), e_slave(1), 4 * 25 * 12 * steps, reply, 0,0, 0)

        do while(reply .ne. 8)
        end do

        ae_slave = 0.
        asi_slave = 0.
        awf_slave = 0.
        awk_slave = 0.
        ark_slave = 0.

        do 99999 count = 1, steps

            if (nsp_slave(count) .ne. 1) cycle

            do 200 k = 1, kld
                k1 = k + 1
                i = k - kl + 1
                i1 = i + 1
                dwkk = dwk_slave(k)
                wfk = wf_slave((count - 1) * 31 + k)   !(k, ia, ic)
                wfk1 = wf_slave((count - 1) * 31 + k1) !(k1, ia, ic)
                wsk = zpi * wfk
                wsk1 = zpi * wfk1
                wkk = wk_slave(k)
                wkk1 = wk_slave(k1)
                do 200 j = 1, jl
                    if (k .lt. kl) then
                        ekj = e_slave((count - 1) * 25 * 12 + (j - 1) * kl + k)     !(k, j, ia, ic)
                        ekj1 = e_slave((count - 1) * 25 * 12 + (j - 1) * kl + k1)   !(k1, j, ia, ic)
                    else
                        ekj = e_slave((count - 1) * 25 * 12 + (j - 1) * kl + kl) * wkh_slave(i)    !(kl, j, ia, ic)
                        ekj1 = e_slave((count - 1) * 25 * 12 + (j - 1) * kl + kl) * wkh_slave(i1)  !(kl, j, ia, ic)
                    endif
                    ae_slave(count)=ae_slave(count)+(ekj+ekj1)*dwkk
                    awf_slave(count)=awf_slave(count)+(ekj*wfk+ekj1*wfk1)*dwkk
                    asi_slave(count)=asi_slave(count)+(ekj/wsk+ekj1/wsk1)*dwkk
                    awk_slave(count)=awk_slave(count)+(ekj*wkk+ekj1*wkk1)*dwkk
                    ark_slave(count)=ark_slave(count)+(ekj/sqrt(wkk)+ekj1/sqrt(wkk1))*dwkk
            200         continue

            asi_slave(count)=ae_slave(count)/asi_slave(count)
            awf_slave(count)=awf_slave(count)/ae_slave(count)
            awk_slave(count)=awk_slave(count)/ae_slave(count)
            ark_slave(count)=(ae_slave(count)/ark_slave(count))**2
        99999   continue

        reply = 0

        call athread_put(0, ae_slave(1), ae(ia, ic),  4 * steps, reply, 0, 0)
        call athread_put(0, asi_slave(1), asi(ia, ic),  4 * steps, reply, 0, 0)
        call athread_put(0, awf_slave(1), awf(ia, ic),  4 * steps, reply, 0, 0)
        call athread_put(0, awk_slave(1), awk(ia, ic),  4 * steps, reply, 0, 0)
        call athread_put(0, ark_slave(1), ark(ia, ic),  4 * steps, reply, 0, 0)

        do while(reply .ne. 5)
        end do

    9999    continue

!==========================================================================================================================

end subroutine mean2_slave

```

## 结语

经过这次比赛，认识到了自己和顶尖选手的差距。不过差距也没有到达天壤之别的地步，希望明年能够提前多做准备，能够让华科和自己不要这样的丢脸。加油！
