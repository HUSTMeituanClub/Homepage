Title: simple_os_book lab1 记录w
Date: 2017-06-02 10:37
Tags: os
Authors: Huatian Zhou
Category: OS


# ucore OS lab 1

ucore os 实验一



### 0x01 Setting up Environment

使用的 Linux 发行版是 `Arch Linux` 。

安装 `qemu` 以及附带的多平台支持：

``` shell
# pacman -S qemu qemu-arch-extra
```

安装完毕之后，就可以使用`qemu-system-i386`模拟器了。

注意要安装`gcc-multilib`，否则无法交叉编译`i386`的可执行文件。

``` shell
# pacman -S gcc-multilib
```

提示 `Replace gcc` 的时候，可以放心大胆地选择`yes`。

这样，在lab01文件夹下直接`make`，就可以直接编译了。



### 0x02 Makefile (Makefile)

环境设置直接略过，直接跳到具体生成`img`文件的指令：



``` shell
gcc -Iboot/ -fno-builtin -Wall -ggdb -m32 -gstabs -nostdinc  -fno-stack-protector -Ilibs/ -Os -nostdinc -c boot/bootasm.S -o obj/boot/bootasm.o
gcc -Iboot/ -fno-builtin -Wall -ggdb -m32 -gstabs -nostdinc  -fno-stack-protector -Ilibs/ -Os -nostdinc -c boot/bootmain.c -o obj/boot/bootmain.o
ld -m    elf_i386 -nostdlib -N -e start -Ttext 0x7C00 obj/boot/bootasm.o obj/boot/bootmain.o -o obj/bootblock.o
```

编译、链接 bootloader 。注意这里的`-nostdlib`和`-e start -Ttext 0x7c00`是使得链接结果能够作为 bootloader 的关键。

``` shell
dd if=/dev/zero of=bin/ucore.img count=10000
dd if=bin/bootblock of=bin/ucore.img conv=notrunc
```

将 bootloader 复制到前512个字节（第一扇区）中。系统在启动前会把这里的代码读到0x7c00处，然后 CPU 从此处开始执行。



### 0x03 Bootloader Code (bootasm.S)



第 15 行：

``` assembly
.code16    # Assemble for 16-bit mode
```

指示 `gas` 编译器生成16位代码。

当`BIOS`刚刚将控制权转交给加载到地址`0x7c00`的`bootloader`的时候，CPU 仍然运转在16位模式。在这种情况下，由于所有寄存器仍然是32位的，所以你不得不在每个指令后加长度限定符。但是通过使用`.code16`，`gas`编译器会认为你正在试图生成一段在16位模式下运行的32位程序，所以会自动帮你加上长度限定符。



第 16,17 行：

``` assembly
cli      # Disable interrupts
cld      # String operations increment
```

开始启动流程。`cli`指令关闭中断，以免初始化过程出现异常。`cld`指令将`DF`清0。

`DF`指示多字节操作时的操作顺序，是从低字节到高字节（increment,clear） 还是高字节到低字节(decrement,set)。

C 运行环境假设`DF`处于被清零状态。所以若要试图载入 C 运行环境，需要把`DF`清零。



第 20~23 行：

``` assembly
xorw %ax, %ax
movw %ax, %ds
movw %ax, %es
movw %ax, %ss
```

初始化数据段寄存器。首先对自身`xor`将自己的值变为0,然后使用`ax`依次清空`DS`,`ES`和`SS`。



第 29～43 行：

``` assembly
seta20.1:
    inb $0x64, %al
    testb $0x2, %al
    jnz seta20.1

    movb $0xd1, %al
    outb %al, $0x64

seta20.2:
    inb $0x64, %al                                 
    testb $0x2, %al
    jnz seta20.2

    movb $0xdf, %al   
    outb %al, $0x60
```

关闭 Intel 的 8086 兼容模式，使得 CPU 能够寻址 1MB 以上的内存空间。

关闭的方式是 Intel 规定的，所以没什么好说。值得一提的是按端口 I/O 操作的方式：

读取端口状态-查看是否繁忙-繁忙则等待-不繁忙则输出。



第 49~52 行：

```assembly
lgdt gdtdesc
movl %cr0, %eax
orl $CR0_PE_ON, %eax
movl %eax, %cr0
```

对应的代码段：第78~86行：

``` assembly
.p2align 2
gdt:
	SEG_NULLASM
	SEG_ASM(STA_X|STA_R,0x0,0xffffffff)
	SEG_ASM(STA_W,0x0,0xffffffff)

gdtdesc:
	.word 0x17
	.long gdt
```

使用`lgdt`指令加载全局描述符表。

`.p2align x`指示`gdt`按2^*x*字节对齐。`gdt`段使用宏定义了三个全局描述符： NULL , CODE 和 DATA ，后两个段分别具有 X*(eXecute)*|R*(Read)* 和 W*(Write)*|R*(Read)* 权限。注意后一个只需要声明 W 就可以了。

`gdtdesc`指示`lgdt`指令应该如何读入全局描述符表。其中`.word a`的a是`gdt`的长度-1（`sizeof(gdt)-1`）。注意这里的`.word 0x17`即是十进制的`23` 。参考了一下`xv6`的 bootloader 之后，建议使用如下这种写法：

``` assembly
	.word (gdtdesc - gdt - 1)
```

第 50~52 行将 *保护模式的开启位* 置为1。至此，CPU 已经做好了进入保护模式的准备。

第 56 行：

``` assembly
	ljmp $PROT_MODE_CSEG, $protcseg
```

使用`ljmp`*(长跳转)*指令进入保护模式。其中：

`$PROT_MODE_CSEG`是保护模式下代码段对应的段选择子(定义位于`asm.h`，值为`0x8`)，这个选择子在`ljmp`指令下将被放置到`CS`中，`$protcseg`的值将被放置到`EIP`中。

值得注意的是段选择子的结构：

长度为`16`位*(`word`)*，*(从后往前)*第0-1位是请求特权级*(RPL)*，第3位是[0:全局描述符表,1:局部描述符表]*(注意局部描述符表在实验中没有涉及)*



第 58~71 行：

``` assembly
.code32
protcseg:
	movw $PROT_MODE_DSEG,%ax
	movw %ax,%ds
	movw %ax,%es
	movw %ax,%fs
	movw %ax,%gs
	movw %ax,%ss


	movl $0x0,%ebp
	movl $start,%esp
    call bootmain
```

这段代码初始化栈寄存器并跳转到`C`代码。

第 62~66 行：使用数据段选择子初始化所有数据栈寄存器。

第 69 行：将`EBP`置 0 。因为`C`代码仍然是 bootloader 的一部分，所以栈仍然使用 bootloader 的栈。由内存模型，bootloader 的栈位于0x0到0x7c00(`$start`，第一条指令)之间。

第 70 行：将`$start`放入`ESP`。

第 71 行：进入`C`代码。



### 0x04 Bootloader Code(bootmain.c)



这段代码阐述 bootloader 如何从硬盘中读取 ELF 格式的 kernel 并且载入内存中执行的。

首先，将 kernel 写入硬盘 ：

` Makefile` :

``` shell
dd if=bin/kernel of=bin/ucore.img seek=1 conv=notrunc
```

注意参数 `seek=1` 代表跳过 `of` 指定文件的第一个 `block` 。`dd` 命令默认 `block` 大小为 `512 Bytes` 。

注意：bootloader 被放置在硬盘的前 `512 Bytes` 中。

`conv=notrunc` 参数防止了 `of` 指定的文件被清空。



`bootmain.c` :

ln 89:

``` c
readseg((uintptr_t)ELFHDR, SECTSIZE * 8, 0)
```



readseg 函数定义：

``` c
static void readseg(uintptr_t va, uint32_t count, uint32_t offset) {
    uintptr_t end_va = va + count;

    va -= offset % SECTSIZE;

    uint32_t secno = (offset / SECTSIZE) + 1;

    for (; va < end_va; va += SECTSIZE, secno ++) {
        readsect((void *)va, secno);
    }
}
```



readsect 函数定义：

``` c
static void
readsect(void *dst, uint32_t secno) {
    waitdisk();

    outb(0x1F2, 1);                         
    outb(0x1F3, secno & 0xFF);
    outb(0x1F4, (secno >> 8) & 0xFF);
    outb(0x1F5, (secno >> 16) & 0xFF);
    outb(0x1F6, ((secno >> 24) & 0xF) | 0xE0);
    outb(0x1F7, 0x20);                      

    waitdisk();

    insl(0x1F0, dst, SECTSIZE / 4);
}
```



首先解释 `readsect` 函数。一系列的 `outb` 指令都是对 `IDE` 硬盘的读写操作，是规定的。

`insl(a,b,c)` 指令将 c 个 `dword` (即 `c*4` 个 `byte` )从端口 a 读入到 b 指向的内存中。

接着是 `readseg` 函数。

注意 `va-=offset%SECTSIZE` 语句。这一行将 `va` 与扇区边界对齐，然后在读取时一次读入一个扇区。

再由原来未修改过的 `va` 指针访问内存，`offset` 就自动加上了。

下一行计算出`offset` 对应的扇区编号。注意这里已经跳过了 bootloader 所在的 `sect 0` 。

然后就是循环调用 `readsect` 读取磁盘内容了。

回到 `bootmain` 的 89 行。`readseg((uintptr_t)ELFHDR, SECTSIZE*8, 0)` 从硬盘中读取 8 个 sect 到内存地址 `ELFHDR` (0x10000，内核放置位置)中。



ln 92 ~ 94:

```c
if (ELFHDR->e_magic != ELF_MAGIC){
  goto bad;
}
```

(struct好评 magic number go die)

测试是否与 `ELF_MAGIC` 相同(即 是不是 ELF 可执行文件)



ln 99~103

```c
ph = (struct proghdr*)((uintptr_t)ELFHDR+ELFHDR->e_phoff);
eph = ph + ELFHDR->e_phnum;
for(;ph<eph;ph++){
  readseg(ph->p_va & 0xFFFFFF,ph->p_memsz,ph->p_offset);
}
```

依次将各个程序段读入内存中相应位置。

ln 107

``` c
((void (*)(void))(ELFHDR->e_entry & 0xFFFFFF))();
```

将入口点转换为 `void (*)(void)` 类型的函数指针，然后调用之，进入内核。



### 0x05 print_stackframe (kdebug.c)

先上我的实现：

``` c
	uint32_t ebpv = read_ebp();
    uint32_t eipv = read_eip();
    while(ebpv){
        cprintf("EBP %08x:EIP %08x:args ",ebpv,eipv);
        uint32_t iter=0;
        for(;iter<4;iter++){
            cprintf("%d ",*(((uint32_t*)ebpv)+iter+2));
        }
        cprintf("\n");
        print_debuginfo(eipv-1);
        // pop
        eipv=*((uint32_t*)ebpv+1);
        ebpv=*(uint32_t*)ebpv;
    }
```

只要熟悉调用栈结构就可以轻易写出。注意这里我写的时候脑子抽了一下，调用栈是由上往下增长的，最高位地址是栈顶，所以访问之前压栈的东西必是`+`。最后一个的 `EBP` 对应位置为0 ，它是 `bootmain.c` 里面的第一个 C 环境函数，C 编译器为它生成的第一个语句 `push ebp` 将在 `bootasm.S` 中初始化的 `movl $0x0, %ebp` 压入栈中。所以`ebpv==0` 为退出条件。



### 0x06 Interrupt (IDT Structure/Gate Descriptors)

每一个中断门描述符由 64 bits (8 bytes) 组成。

#### 80386 Task Gate Descriptor

`Task Gate` 主要用于任务切换。

00-15 `NOT USED`

16-31 `段选择子 Selector`

32-39 `NOT USED`

40-44 二进制序列 `10100`

45-46 DPL (Descriptor Privilege Level)

47 Present

48-63 `NOT USED`



#### 80306 Interrupt Gate Descriptor

`Interrupt Gate` 主要用于中断处理

00-15 `Offset 段内偏移`

16-31 `段选择子 Selector`

32-36 `NOT USED`

37-44 二进制序列 `00001110`

45-46 DPL (Descriptor Privilege Level)

47 Present

48-63 `Offset 段内偏移`



#### 80386 Trap Gate Descriptor

`Trap Gate` 主要用于系统调用

00-15 Offset 段内偏移

16-31 段选择子 Selector

32-36 NOT USED

37-44 二进制序列 00011110

45-46 DPL (Descriptor Privilege Level)

47 Present

48-63 Offset 段内偏移



### 0x07 Interrupt (Initialize IDT)

```c
extern uintptr_t __vectors[];
int i;
for(i=0;i<256;i++){
    SETGATE(idt[i],(i==T_SYSCALL),GD_KTEXT,__vectors[i],3*(i==T_SYSCALL));
}
lidt(&idt_pd);
```

直接上实现。

注意 `SETGATE` 宏的 `seg` 参数指的是段选择子。所以直接使用 `GD_KTEXT` 。

这里判断 `i==T_SYSCALL` 用于设置用于系统调用的陷阱门描述符。

最后 `lidt` 指令加上 `idt_pd` 的地址加载 `IDT`



### 0x08 Interrupt (Clock Interrupt Lab)

实现没有什么好说的。这里说一下这个东西的流程吧。

中断描述符表初始化完毕后，所有中断例程最后都指向了 `trapentry.S` 里的 `__alltraps:` 标签。

`__alltraps` 进行一些信息压栈后，通过 `push esp` 将当前栈顶指针变成函数参数(回想：调用栈)。注意由于压栈操作，当前栈顶指针可以视作一个结构体指针。最后调用 `trap.c` 中的函数 `trap(tf)` 。

而 `trap` 调用函数 `trap_dispatch` 进行分发 (蛇计模式 (笑。



### 0x09 Extend-1 Switching from Kernel Mode to User Mode

先上一手实现。

``` c
if(tf->tf_cs != USER_CS){
            struct trapframe tmp=*tf;
            tmp.tf_cs=USER_CS;
            tmp.tf_ds=tmp.tf_es=tmp.tf_ss=USER_DS;
            tmp.tf_esp=(uint32_t)tf+sizeof(struct trapframe)-8;
            tmp.tf_eflags |= (3<<12);
            *((uint32_t*)tf-1)=(uint32_t)&tmp;
        }
```

解释一下这个过程：

首先我们建立临时数据结构 `tmp` 。

之所以不直接在 `tf` 上魔改，是因为 `tf` 本身没有我们需要的 `tf_esp` 和 `tf_ss` 。

没有的原因是中断处于 `Ring 0` ，而触发中断的代码也在 `Ring 0` 。

接下来改变 `cs` 和 `ds es ss` 寄存器到相应的用户段。

接下来设置用户栈栈顶 `esp` 。在这里我们把它放在压入 `tf` 之前的位置。

如果不这样做，`tf` 这块数据就会释放不掉。

接下来改变 `eflags` 的 `I/O` 特权位。这使得用户权限可以使用 `I/O` 指令。

最后一步改变原先的 `tf ` 指针。要理解这一步的原因，需要观察 `trapentry.S` 。

``` asm
# push %esp to pass a pointer to the trapframe as an argument to trap()
    pushl %esp

    # call trap(tf), where tf=%esp
    call trap

    # pop the pushed stack pointer
    popl %esp

    # return falls through to trapret...
.globl __trapret
__trapret:
    # restore registers from stack
    popal

    # restore %ds, %es, %fs and %gs
    popl %gs
    popl %fs
    popl %es
    popl %ds

    # get rid of the trap number and error code
    addl $0x8, %esp
    iret
```

这里，在 `call trap` 之前，把 `esp` 压栈作为`trap()` 的参数传给 `trap()` 。

在调用过程结束后，把压栈的参数弹栈变为 `esp` 的值。

此时，我们如果改变栈顶内容，那么这里弹栈，就会将我们的 `tmp` 结构当作栈顶，从而从我们的 `tmp` 结构恢复各寄存器值。

最后，CPU 检测到特权级转换，再从我们的 `tmp` 结构中弹出 `esp` 和 `ss` 。这时，我们修改过的 `tf_esp` 产生作用，将 `esp` 寄存器设定在我们想要的值上。

至此，整个特权级转换的过程就完成了。

### 0x0A Extend-1 Switching from User Mode to Kernel Mode

照例来一手实现。

```c
if(tf->tf_cs != KERNEL_CS){
            tf->tf_cs=KERNEL_CS;
            tf->tf_ds = tf->tf_es = tf->tf_ss = KERNEL_DS;
            tf->tf_eflags &= ~(3<<12);
            struct trapframe *tmp=(struct trapframe*)(tf->tf_esp-sizeof(struct trapframe)+8);
            memmove(tmp,tf,sizeof(struct trapframe)-8);
            *((uint32_t*)tf-1)=(uint32_t)tmp;
}
break;
```

首先可以看到，和上一个不一样，这次 `tf` 已经包含了我们需要的所有信息。所以可以直接修改 `tf` 的值。

这里 `tmp` 指针的位置是用户栈上分配了一块内存。这里需要注意的是，由于后一步没有特权转换，所以不需要最后两个值。

之后把需要的数据 `memmove` 到需要的位置。这里不直接使用 `tf` 的原因是不好确定 `tf` 和 `tf_esp` 的位置。



### 0x0B Extend-1 Notice

增加中断处理代码后，要把中断 `T_SWITCH_TOK` 的特权级设为 `Ring 0` ，否则无法触发中断。



### 0x0C Extend-2 Trigger Switching by Keyboard Input

```c
case IRQ_OFFSET + IRQ_KBD:
        c = cons_getc();
        cprintf("kbd [%03d] %c\n", c, c);
        switch(c){
            case '3':
                if(tf->tf_cs != USER_CS){
                    tf->tf_cs=USER_CS;
                    tf->tf_ds=tf->tf_es=tf->tf_ss=USER_DS;
                    tf->tf_eflags|=(3<<12);
                    print_trapframe(tf);
                }
            break;
            case '0':
                if(tf->tf_cs != KERNEL_CS){
                    tf->tf_cs=KERNEL_CS;
                    tf->tf_ds=tf->tf_es=tf->tf_ss=KERNEL_DS;
                    tf->tf_eflags&=~(3<<12);
                    print_trapframe(tf);
                }
            break;
            default:break;
        }
        break;
```

没什么好说的。注意硬件中断是在内核态触发的，所以直接魔改 `tf` 应该就可以了。
