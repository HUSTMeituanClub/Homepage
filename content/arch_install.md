Title: 以官方Wiki的方式安装ArchLinux
Date: 2017-05-17 23:26:29
Category: Linux
Tags: arch, linux 
Authors: Di Wu


## 写在前面

>   **这可能是你能找到的最适合你的中文`ArchLinux`安装教程。**

前几天硬盘挂了，万幸的是家目录放在了另一块硬盘上所以存活了下来。不得不再重装一遍`Arch`，算上帮朋友装的，这已经是我第四次安装`Arch`了。也想借此机会记录这个过程写一篇完全按照官方Wiki指导再加上Wiki上没有重点写出来但是安装过程中会遇到的一些问题的一篇不太一样的安装教程。

<!--more-->

很多人提起起`Arch`的第一反应就是安装困难，这种困难有很多原因，也就是接下来我们将会面对的问题。

*   没有图形界面的引导：`Arch`只给我们提供了一个最小的环境，所有的安装操作都需要在命令行中完成，这对于不习惯命令行操作的人来说是最难以跨越的一个坎。许多发行版之所以可以流行开来就是因为他们提供了友好的、流程化的安装过程，这帮很多人解决了学习`Linux`的第一步：安装一个`Linux`。
*   预备知识的不足与缺乏查找并解决问题的能力：一些对于安装系统比较重要的知识例如系统引导、配置文件的编辑、简单的命令行操作等没有接触过，所以操作时往往摸不着头脑，一旦自己的操作结果与教程不符便不知道如何去解决遇到的问题。
*   缺乏合适的教程：安装Arch最好的也是最完备的教程就是官方的[Installation guide](https://wiki.archlinux.org/index.php/installation_guide)与[Wiki](https://wiki.archlinux.org/)，虽然部分内容有中文版，但是中文的翻译有些时候会落后于英文版，不推荐完全依赖于中文Wiki。并且官方Wiki的写作方式更偏向于文档，没有我们所习惯的按步骤编排的安装过程，给不熟悉这种写作方式的同学造成了阅读与使用上的困难。国内的可以找到的教程往往都是时间比较久远，或是没有提及或是忽略了一些新手容易犯错误的地方。

>   **本篇教程致力于与现有的Wiki保持一致，并且适当地加入一些适合初学者学习的链接，希望可以让阅读了这篇教程的同学可以提高自己利用现有及以后可能出现的新的Wiki内容的能力。**

`ArchLinux`或者是`Linux`的优点就不在这里多说了，我相信打开这篇教程的同学一定可以从这样的过程中得到很多。

下面就正式开始我们的教程。

## 安装教程

### 前期准备

#### 安装介质

在安装之前我们先要准备一个安装介质，在这里只推荐U盘作为安装介质。

1.  到[https://www.archlinux.org/download/](https://www.archlinux.org/download/)页面下方的中国镜像源中下载`archlinux-**-x86_64.iso`这个`iso`文件。 

2.  *   如果是`Linux`系统下制作安装介质，推荐使用`dd`命令，教程：

>   http://blog.topspeedsnail.com/archives/404

*   如果是`windows`系统下制作安装介质，推荐使用`usbwriter`这款轻量级的工具，下载链接：

>   https://sourceforge.net/projects/usbwriter/

#### 磁盘准备

我们需要有一块空闲的磁盘区域来进行安装，这里的空闲指的是**没有被分区**的空间。下面来介绍如何准备这块空间。

*   在`windows`下空出一块分区来安装：利用`windows`自带的磁盘管理工具就可以：

1.  右击`windows`图标，在弹出菜单中选择磁盘管理（其他版本的`windows`请自行找到打开磁盘管理的方式）：

![](/images/arch01.jpeg)

2.  右击想要删除的分区，选择删除卷（注意这步之后这个分区的所有数据将会丢失）：

![](/images/arch02.jpeg)

*   在`linux`下分出一块区域安装：使用`fdisk`进行，教程请见链接中的删除分区：

>   http://www.liusuping.com/ubuntu-linux/linux-fdisk-disk.html

*   空闲的磁盘（新磁盘）：不需要进行任何操作。

### U盘安装

下面的过程实际上都在刚刚准备好的U盘启动介质上的`Linux`系统下进行，所以**启动时都应该选择U盘**。

#### 设置启动顺序

这一步在不同品牌的电脑上都不一样，所以需要大家自行搜索**自己电脑品牌+启动顺序**这个关键词来进行设置。

例如我的电脑搜索神舟 启动顺序可以得到如下的结果：

>   https://zhidao.baidu.com/question/170954184.html

一般来说现在的主板都可以不用进入BIOS而快速地切换启动顺序，只要找到相应的快捷键就可以了。

#### 进入U盘下的Linux系统

1.  按上一步设置好启动顺序，启动之后会看到如下界面：

![](/images/arch03.jpeg)

如果直接进入`windows`，请检查启动顺序是否设置成功，U盘是否在制作启动介质时成功写入。

如果没有看到这个界面，请检查U盘是否制作成功，如果多次遇到问题可以考虑换一个U盘。

选择第一个选项。

2.  这时`Arch`开始加载，你将会看到屏幕显示如下内容：

![](/images/arch04.jpeg)

加载完成后你将会进入一个有命令提示符的界面：

![](/images/arch05.jpeg)

如果出现`FAIL`或是其他错误信息导致无法启动请自行搜索错误信息来获得解决方法。

这就是`Linux`的终端界面了，接下来我们将通过在这个界面执行一系列命令来将`Arch`安装到我们的磁盘上。

---

下面进行的过程是按照官方[Installation guide](https://wiki.archlinux.org/index.php/installation_guide)为依据进行的，出现的任何问题都可以到链接中的相应部分查找原文找到解决方式。

#### 检查引导方式

目前的引导方式主要分为EFI引导+GPT分区表与BIOS(LEGACY)引导+MBR分区表两种，几乎比较新的机器都采用了EFI/GPT引导的方式。关于这部分的内容如果有兴趣可以通过这个链接进行了解：

>   http://www.chinaz.com/server/2016/1017/595444.shtml

如果你不知道自己的引导方式，请在命令提示符下执行以下命令：

```bash
ls /sys/firmware/efi/efivars
```

这里的`ls`是命令，空格后面的一串为路径，作为`ls`命令的参数。`ls`命令的作用是显示路径目录下的所有的文件（夹）。

---

如果你对命令行下的常用操作（TAB补全、取消命令等）不熟悉，请先学习了解下面部分实用的快捷键或命令：

>   **Tab键 命令行自动补全。键入命令或文件名的前几个字符，然后按 [Tab] 键，它会自动补全命令或显示匹配你键入字符的所有命令**
>
>   ↑(Ctrl+p) 显示上一条命令
>
>   ↓(Ctrl+n) 显示下一条命令
>
>   Ctrl-C: 终止当前正在执行的命令

---

输入命令并回车执行后，如果提示

```bash
ls: cannot access '/sys/firmware/efi/efivars': No such file or directory
```

表明你是以BIOS方式引导，否则为以EFI方式引导。现在只需要记住这个信息，之后会用到。

#### 联网

`arch`并不能离线安装，因为我们需要联网来下载需要的组件，所以我们首先要连接网络。

*   如果你是有线网并且路由器支持DHCP的话插上网线后应该已经是联网状态了，可以执行以下命令来进行判断：

```bash
ping www.baidu.com
```

如果可以看到类似下面的内容就说明连上了网络：

![](/images/arch05.jpg)

>   再次提示用快捷键Ctrl-C可以终止当前正在执行的命令

*   如果你是无线网，请执行以下命令：

```bash
wifi-menu
```

这是一个实用的命令行下联网工具，有字符形式的图形化界面，利用它可以方便地联网，如果它没能起作用，需要进入以下页面查找解决方式：

>   https://wiki.archlinux.org/index.php/Wireless_network_configuration

连接以后同样可以通过上面的`ping`命令来进行测试。

#### 更新系统时间

执行如下命令：

```bash 
timedatectl set-ntp true
```

>   正常情况下这样的命令并没有输出，所谓没有消息就是最好的消息

#### 分区与格式化

**特别注意：涉及到分区与格式化的操作要格外注意，命令在回车之前请再三确认知道自己在做什么，并且没有输错命令，否则将会来带来数据的丢失！如果有需要在操作之前请备份重要的数据。**

但是我们也并不要过于惧怕分区与格式化过程，正确操作的情况下不会对你其他数据产生任何影响。

##### 查看目前的分区情况

执行命令：

```bash
fdisk -l
```

以我的电脑为例：

![](/images/arch06.jpg)

可以看到我的一块238.5g的硬盘(`/dev/sda`就代表这块硬盘)，下面列出了`/dev/sda*`这三个分区，`/dev/sda3`是我存活下来的家目录，可以看到它的类型为`Linux`分区。注意看`Start`与`End`的数值，这个数值代表扇区号，可以理解成硬盘被划分成了一个个小单元，可以直观地看出来在`/dev/sda2`的`End`与`/dev/sda3`的`Start`之间空出了一大块未分配的空间，接下来我们将分配这块区域。

---

*   如果你是BIOS/MBR方式引导，**跳过下面创建一个引导分区**的步骤。
*   如果你是EFI/GPT方式引导，并且同时安装了其他系统，那么你应该可以在分区列表中发现一个较小的并且类型为EFI的分区，这是你的引导分区，请记下它的路径（/dev/sdxY)备用，**跳过下面创建一个引导分区**的步骤。
*   如果你是EFI/GPT方式引导，但是没有这个较小的并且类型为EFI的引导分区（这种情况一般只会出现在新的硬盘），那么你需要**先创建一个引导分区**。

---

##### 创建一个引导分区（**仅上面所列的第三种情况需要进行这步**）

执行命令：

```bash
fdisk /dev/sdx （请将sdx替换成你要操作的磁盘如sdb sdc等）
```

下面你就进入了`fdisk`的操作环境， 输入`m`并回车可以查看各命令的作用。

1.  如果你是一块全新的硬盘，输入`g`来创建一个全新的gpt分区表。

2.  输入`n`创建一个新的分区，首先会让你选择起始扇区，一般直接回车使用默认数值即可，然后可以输入结束扇区或是分区大小，这里我们输入`+512M`来创建一个512M的引导分区。

3.  这时我们可以输入`p`来查看新创建的分区。

4.  输入`t`并选择新创建的分区序号来更改分区的类型，输入`l`可以查看所有支持的类型，输入`ef`更改分区的类型为`EFI`。

5.  输入`w`来将之前所有的操作写入磁盘生效，在这之前可以输入`p`来确认自己的分区表没有错误。

6.  输入以下命令来格式化刚刚创建的引导分区：

```bash
mkfs.fat -F32 /dev/sdxY （请将的sdxY替换为刚创建的分区）
```

现在引导分区就创建好了。

##### 创建根分区

输入命令：

```bash
fdisk /dev/sdx （请将sdx替换成你要操作的磁盘如sdb sdc等）
```

1.  如果你是一块全新的硬盘，输入`o`来创建一个新的MBR分区表。

2.  输入`n`创建一个新的分区，首先会让你选择起始扇区，一般直接回车使用默认数值即可，然后可以输入结束扇区或是分区大小，如果我们想要使创建的分区完全占满空闲的空间，可以直接回车使用默认结束扇区。

3.  这时我们可以输入`p`来查看新创建的分区。

4.  输入`w`来将之前所有的操作写入磁盘生效，在这之前可以输入`p`来确认自己的分区表没有错误。

5.  输入以下命令来格式化刚刚创建的根分区：

```bash
mkfs.ext4 /dev/sdxY （请将的sdxY替换为刚创建的分区）
```

这是我的分区过程供参考：

![](/images/arch07.jpg)

![](/images/arch08.jpg)

#### 挂载分区

执行以下命令将根分区挂载到`/mnt`：

```bash
mount /dev/sdxY /mnt （请将sdxY替换为之前创建的根分区）
```

---

**如果你是EFI/GPT引导方式**，执行以下命令创建/boot文件夹并将引导分区挂载到上面。**BIOS/MBR引导方式无需进行这步。**

```bash
mkdir /mnt/boot
mount /dev/sdxY /mnt/boot （请将sdxY替换为之前创建或是已经存在的引导分区）
```

---

#### 选择镜像源

因为从这步开始，需要进行一些编辑配置文件的操作，所以需要掌握一些命令行下非常著名的一款编辑器`Vim`的基本操作，在这里推荐学习下面这个链接中的存活部分，可以完成编辑、复制粘贴与保存工作即可。

>   http://coolshell.cn/articles/5426.html

---

镜像源是我们下载的软件包的来源，我们需要根据自己的地区选择不同的源来加快下载的速度。

执行以下命令，用`Vim`来编辑`/etc/pacman.d/mirrorlist`这个文件

```bash
vim /etc/pacman.d/mirrorlist
```

>   提示：输入路径时可以用`Tab`键补全

![](/images/arch09.jpg)

找到标有`China`的镜像源，`normal`模式下按下`dd`可以剪切光标下的行，按`gg`回到文件首，按`p`将行粘贴到文件最前面的位置（优先级最高）。

当然也可以直接手工输入。

这里推荐使用清华、浙大源：

```
Server = http://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
Server = http://mirrors.zju.edu.cn/archlinux/$repo/os/$arch
```

最后记得用`:wq`命令保存文件并退出。

#### 安装基本包

下面就要安装最基本的`ArchLinux`包到磁盘上了。这是一个联网下载并安装的过程。

执行以下命令：

```bash
pacstrap /mnt base base-devel
```

根据下载速度的不同在这里需要等待一段时间，当命令提示符重新出现的时候就可以进行下一步操作了。

#### 配置Fstab

生成自动挂载分区的`fstab`文件，执行以下命令：

```bash
genfstab -L /mnt >> /mnt/etc/fstab
```

由于这步比较重要，所以我们需要输出生成的文件来检查是否正确，执行以下命令：

```bash
cat /mnt/etc/fstab
```

![](/images/arch10.jpg)

如图，可以看到`/dev/sda4`被挂载到了根分区。

`/dev/sda3`是我之前存活下来的家目录被挂载到了`/home`目录（你们没有这条）。

**如果是`EFI/GPT`引导的还应该有引导分区被挂载到`/boot`目录**。

#### Chroot

`Chroot`意为`Change root`，相当于把操纵权交给我们新安装（或已经存在）的`Linux`系统，**执行了这步以后，我们的操作都相当于在磁盘上新装的系统中进行**。

执行如下命令：

```bash
arch-chroot /mnt
```

---

这里顺便说一下，如果以后我们的系统出现了问题，只要插入U盘并启动， 将我们的系统根分区挂载到了`/mnt`下，再通过这条命令就可以进入我们的系统进行修复操作。

---

#### 设置时区

依次执行如下命令设置我们的时区为上海并生成相关文件：

```bash
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
hwclock --systohc
```

![](/images/arch11.jpg)

#### 设置Locale

设置我们使用的语言选项，执行如下命令来编辑`/etc/locale.gen`文件：

```bash
vim /etc/locale.gen
```

---

等等，怎么提示`bash:vim:command not found`了？

因为我们现在已经`Chroot`到了新的系统中，只有一些最基本的包（组件），这时候我们就需要自己安装新的包了，下面就要介绍一下`ArchLinux`下非常强大的包管理工具`pacman`，大部分情况下，一行命令就可以搞定包与依赖的问题。

安装包的命令格式为`pacman -S 包名`，`pacman`会自动检查这个包所需要的其他包（即为依赖）并一起装上。下面我们就通过`pacman`来安装一些包，这些包在之后会用上，在这里先提前装好。

执行如下命令：

```bash
pacman -S vim dialog wpa_supplicant
```

一路确认之后包就被成功装上了。

![](/images/arch12.jpg)

图中只安装了`Vim`和它的依赖。

---

安装好`Vim`以后，再次执行：

```bash
vim /etc/locale.gen
```

在文件中找到`zh_CN.UTF-8 UTF-8` `zh_HK.UTF-8 UTF-8` `zh_TW.UTF-8 UTF-8``en_US.UTF-8 UTF-8`这四行，去掉行首的#号，保存并退出。如图：

![](/images/arch13.jpg)

![](/images/arch14.jpg)

然后执行：

```bash
locale-gen
```

![](/images/arch15.jpg)

打开（不存在时会创建）`/etc/locale.conf`文件：

```bash
vim /etc/locale.conf
```

在文件的第一行加入以下内容：

```bash
LANG=en_US.UTF-8
```

保存并退出。

#### 设置主机名

打开（不存在时会创建）`/etc/hostname`文件：

```bash
vim /etc/hostname
```

在文件的第一行输入你自己设定的一个`myhostname`

保存并退出。

编辑`/etc/hosts`文件：

```bash
vim /etc/hosts
```

作如下修改（将`myhostname`替换成你自己设定的主机名）

```bash
127.0.0.1	localhost.localdomain	localhost
::1		localhost.localdomain	localhost
127.0.1.1	myhostname.localdomain	myhostname
```

![](/images/arch16.jpg)

这里我设置的是`viseator`。

保存并退出。

#### 设置Root密码

`Root`是`Linux`中具有最高权限帐户，有些敏感的操作必须通过`Root`用户进行，比如使用`pacman`，我们之前进行所有的操作也都是以`Root`用户进行的，也正是因为`Root`的权限过高，如果使用不当会造成安全问题，所以我们之后会新建一个普通用户来进行日常的操作。在这里我们需要为`Root`帐户设置一个密码：

执行如下命令：

```bash
passwd
```

按提示设置并确认就可以了。

![](/images/arch17.jpg)

---

或许有的人已经发现官方Wiki和一些其他教程资料中的命令是以`#`或`$`开头的，这两个符号就对应着命令行中的命令提示符，`#`代表以`Root`用户执行命令，`$`代表以普通用户执行命令，平时使用教程中的命令时应该注意这一点。

---

#### 安装`Intel-ucode`（非`Intel`CPU可以跳过此步骤）

直接`pacman`安装：

```bash
pacman -S intel-ucode
```

#### 安装`Bootloader`

经常听说很多人因为引导问题导致系统安装失败，多数是因为教程没有统一或是过时的教程引起的，这里只要按照步骤来其实是不难的。

这里我们安装最流行的`Grub2`。

*   首先安装`os-prober`这个包，它可以配合`Grub`检测已经存在的系统，自动设置启动选项。

```bash
pacman -S os-prober
```

---

##### **如果为BIOS/MBR引导方式：**

*   安装`grub`包：

```bash
pacman -S grub
```

*   部署`grub`：

```bash
grub-install --target=i386-pc /dev/sdx （将sdx换成你安装的硬盘）
```

注意这里的`sdx`应该为硬盘（例如`/dev/sda`），**而不是**形如`/dev/sda1`这样的分区。

*   生成配置文件：

```bash
grub-mkconfig -o /boot/grub/grub.cfg
```

![](/images/arch18.jpg)

**如果你没有看到如图所示的提示信息，请仔细检查是否正确完成上面的过程。**

---

##### **如果为EFI/GPT引导方式：**

*   安装`grub`与`efibootmgr`两个包：

```bash
pacman -S grub efibootmgr
```

*   部署`grub`：

```bash
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=grub
```

*   生成配置文件：

```bash
grub-mkconfig -o /boot/grub/grub.cfg
```

**提示信息应与上面的图类似，如果你发现错误，请仔细检查是否正确完成上面的过程。**

---

##### 安装后检查

**如果你是多系统，请注意上面一节中对`os-prober`这个包的安装。**

**强烈建议使用如下命令检查是否成功生成各系统的入口，如果没有正常生成会出现开机没有系统入口的情况：**

```bash
vim /boot/grub/grub.cfg
```

检查接近末尾的`menuentry`部分是否有`windows`或其他系统名入口。下图例子中是`Arch Linux`入口与检测到的`windows10`入口（安装在`/dev/sda1`），具体情况可能有不同：

![](/images/arch22.jpg)

**如果你没有看到系统入口或者该文件不存在**，请检查上一小节内容并重新生成配置文件。

**如果你已经安装`os-prober`包并生成配置文件后还是没有生成其他系统的入口**，请参照：

>   [https://wiki.archlinux.org/index.php/GRUB/Tips_and_tricks#Combining_the_use_of_UUIDs_and_basic_scripting](https://wiki.archlinux.org/index.php/GRUB/Tips_and_tricks#Combining_the_use_of_UUIDs_and_basic_scripting) 

编辑配置文件手动添加引导的分区入口。

---

##### 重启

接下来，你需要进行重启来启动已经安装好的系统，执行如下命令：

```bash
exit
reboot
```

注意这个时候你可能会卡在有两行提示的地方无法正常关机，长按电源键强制关机即可，没有影响。

关机后拔出U盘，启动顺序会自动以硬盘启动，如果一切顺利，那么你将会看到下面的界面：

![](/images/arch19.jpg)

启动时有可能会有输出信息显示在这里，直接回车就可以了。

输入`root`，再输入之前设置的密码，显示出命令提示符，恭喜你，你已经成功安装`ArchLinux`！

## 安装后配置

虽然系统安装好了，但是还没有进行基本配置和安装图形界面，所以接下来我们要进行一些必须的配置和图形界面的安装。

请见下一篇文章：[ArchLinux安装后的必须配置与图形界面安装教程](http://www.hustmeituan.club/archlinuxan-zhuang-hou-de-bi-xu-pei-zhi-yu-tu-xing-jie-mian-an-zhuang-jiao-cheng.html)

## 特别感谢

评论区中`Senrey_Song`、`YKun`对于本教程内容的指正。


