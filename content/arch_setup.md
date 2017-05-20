Title: ArchLinux安装后的必须配置与图形界面安装教程
Date: 2017-05-19 21:38:57
Category: Linux
Tags: arch, linux 
Authors: Di Wu

## ArchLinux安装后的必须配置

在[上一篇教程](http://www.hustmeituan.club/yi-guan-fang-wikide-fang-shi-an-zhuang-archlinux.html)中，我们成功地安装了`ArchLinux`，这时系统处于一个非常精简的状态，为了日常使用，我们必须进行一些配置、安装一些需要的组件，来扩展我们的系统功能，开源的组件相互协同工作也是`Linux`的迷人之处之一。

下面的教程部分参考了官方[General recommendations](https://wiki.archlinux.org/index.php/General_recommendations)。

<!--more-->

### 连接网络

现在我们是在新安装的系统上进行操作，所以我们要重新联网，我们在之前安装系统时已经提前装好了相关的包。所以现在只要跟之前一样，执行

```bash
wifi-menu
```

按界面提示进行操作就可以了（有线网用户无视这段）。

同样可以使用`ping`命令来测试是否正常联网。

### 新建用户

在这之前所有操作都是以`root`用户的身份进行的，由于`root`的权限过高，日常使用`root`用户是不安全的。`Linux`为我们提供了强大的用户与组的权限管理，提高了整个系统的安全性。这里我们就来新建一个用户。

执行以下命令来创建一个名为`username`的用户（请自行替换`username`为你的用户名）：

```bash
useradd -m -G wheel username （请自行替换username为你的用户名）
```

在这里稍微解释一下各参数的含义：

`-m`：在创建时同时在`/home`目录下创建一个与用户名同名的文件夹，这个目录就是你的**家目录**啦！家目录有一个别名是`~`，你可以在任何地方使用`~`来代替家目录路径。这个神奇的目录将会用于存放你所有的个人资料、配置文件等所有跟系统本身无关的资料。这种设定带来了诸多优点：

*   只要家目录不变，你重装系统后只需要重新安装一下软件包（它们一般不存放在家目录），然后所有的配置都会从家目录中读取，完全不用重新设置软件着。
*   你可以在家目录不变的情况下更换你的发行版而不用重新配置你的环境。
*   切换用户后所有的设置会从新的用户的家目录中读取，将不同用户的资料与软件设置等完全隔离。
*   有些著名的配置文件比如`vim`的配置文件`~/.vimrc`，只要根据自己的使用习惯配置一次， 在另一个`Linux`系统下（例如你的服务器）把这个文件复制到家目录下，就可以完全恢复你的配置。

`-G wheel`：`-G`代表把用户加入一个组，对用户与组的概念感兴趣的同学可以自行查找有关资料学习。后面跟着的`wheel`就是加入的组名，至于为什么要加入这个组，后面会提到。

当然记得为新用户设置一个密码，执行如下命令：

```bash
passwd username （请自行替换username为你的用户名）
```

根据提示输入两次密码就可以了，注意，这是你的用户密码，推荐与之前设置的`root`用户的密码不同。

### 配置sudo

我们已经创建好了一个新的用户，以后我们将会使用这个用户来登录，那么如果我们需要执行一些只有`root`用户才能执行的命令（例如修改系统文件、安装软件包）怎么办？当然我们可以通过

```bash
su
```

命令来切换到`root`用户执行命令后再通过

```bash
exit
```

返回普通用户。

但是`sudo`为我们提供了一个更快捷的办法，使用`sudo`，我们只要在需要`root`权权限执行的命令之前加上`sudo`就可以了，例如安装软件包：

```bash
sudo pacman -S something
```

下面我们就来安装并配置`sudo`。

`sudo`本身也是一个软件包，所以我们需要通过`pacman`来安装：

```bash
pacman -S sudo
```

接下来我们需要用专门的`visudo`命令来编辑`sudo`的配置文件：

```bash
visudo
```

实际上就是`vim`的操作，使用它是为了对编辑后的文件进行检查防止格式的错误。

![](/images/arch20.jpg)

找到

```bash
# %wheel ALL=(ALL)ALL
```

这行，去掉之前的`#`注释符，保存并退出就可以了。

这里的`%wheel`就是代表`wheel`组，意味着`wheel`组中的所有用户都可以使用`sudo`命令。

当然为了安全使用`sudo`命令还是需要输入**当前用户**的密码的。

配置好`sudo`以后，我们进行一次重启，执行：

```bash
reboot
```

来重启你的电脑。

重启以后输入你**刚创建的用户名与密码**来登录。

## 图形界面的安装

### 显卡驱动的安装

![](/images/arch21.png)

参照这个表格，安装相应的包，比如你是`intel`的集成显卡（绝大多数人的情况），执行：

```bash
sudo pacman -S xf86-video-intel
```

提示：`Nvidia`的独显驱动如非必要，建议只装集成显卡的驱动（省电，如果同时装也会默认使用集成显卡），不容易出现冲突问题。相反，如果集成显卡驱动有问题无法装上，可以装独显驱动，具体的版本请到下面的链接查询：

>   https://wiki.archlinux.org/index.php/Xorg#Driver_installation

### 安装Xorg

`Xorg`是`Linux`下的一个著名的开源图形服务，我们的桌面环境需要`Xorg`的支持。

执行如下命令安装`Xorg`及相关组件：

```bash
sudo pacman -S xorg-server xorg-apps
```

### 安装桌面环境

`Linux`下有很多著名的桌面环境如`Xfce`、`KDE(Plasma)`、`Gnome`、`Unity`、`Deepin`等等，它们的外观、操作、设计理念等各方面都有所不同， 在它们之间的比较与选择网上有很多的资料可以去查。

在这里我们选择笔者使用的`Xfce`和非常流行的`KDE(Plasma)`作为示范，当然你也可以把它们全部装上换着用……因为`Linux`的模块化，这样完全没有问题。

更多桌面环境的安装指南请见下面的链接：

>   https://wiki.archlinux.org/index.php/Desktop_environment#List_of_desktop_environments

#### 安装Xfce

直接安装软件包组（包含了很多软件包）即可：

```bash
sudo pacman -S xfce4 xfce4-goodies
```

#### 安装KDE(Plasma)

直接安装软件包组（包含了很多软件包）即可：

```bash
sudo pacman -S plasma kde-applications kde-l10n-zh_cn
```

### 安装桌面管理器

安装好了桌面环境包以后，我们需要安装一个图形化的桌面管理器来帮助我们登录并且选择我们使用的桌面环境，这里我推荐使用`sddm`。

#### 安装sddm

执行：

```bash
sudo pacman -S sddm
```

#### 设置开机启动sddm服务

这里就要介绍一下`Arch`下用于管理系统服务的命令`systemctl`了，服务的作用就是字面意思，为我们提供特定的服务，比如`sddm`就为我们提供了启动`xorg`与管理桌面环境的服务。

命令的使用并不复杂：

```bash
sudo systemctl start   服务名 （启动一项服务）
sudo systemctl stop    服务名 （停止一项服务）
sudo systemctl enable  服务名 （开机启动一项服务）
sudo systemctl disable 服务名 （取消开机启动一项服务）
```

所以这里我们就执行下面命令来设置开机启动`sddm`：

```bash
sudo systemctl enable sddm
```

### 提前配置网络

到现在我们已经安装好了桌面环境，但是还有一件事情需要我们提前设置一下。由于我们之前使用的一直都是`netctl`这个自带的网络服务，而桌面环境使用的是`NetworkManager`这个网络服务，所以我们需要禁用`netctl`并启用`NetworkManager`：

```bash
sudo systemctl disable netctl
sudo systemctl enable NetworkManager （注意大小写）
```

同时你可能需要安装工具栏工具来显示网络设置图标（某些桌面环境已经装了，但是为了保险可以再装一下）：

```bash
sudo pacman -S network-manager-applet
```

这样开机以后我们就可以在图形界面下配置我们的网络啦。

---

重新启动后，如果你看到桌面管理器的界面，选择你需要的桌面环境并输入用户名与密码登陆后，看到了熟悉而又陌生的桌面，那么恭喜你，你已经完成了桌面环境的安装！

## 你可能需要知道的操作与软件包推荐

到这里，`ArchLinux`的安装与基本配置教程已经结束了，笔者在编写过程中基本凭着多次安装的经验与这次安装的记录完成，难免会有疏漏与不正确的地方，还请大家通过下面的评论或邮件(viseator@gmail.com)提出意见与建议。也欢迎你们与我交流安装的问题。

下面一篇文章将会介绍一些实用的配置（如中文输入法的安装）与软件包等。
