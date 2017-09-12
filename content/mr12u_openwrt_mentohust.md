Title:  TP-Link mr12u-v1刷openwrt+mentohust交叉编译（附文件下载）
Date: 2017-09-05 20:06:16
Category: Openwrt
Tags: openwrt
Authors: Di Wu


## 写在前面

开学学校启用了有线网，由于校园网存在只能单一设备登陆的限制与无线登陆限速，所以想通过路由器刷`openwrt`再使用`mentohust`进行校园网的锐捷认证来实现多设备与不限速使用。

在选择路由器时考虑了如下因素：

1.  可刷`openwrt`：只有特定的处理器支持`openwrt`，支持的路由器型号在官网有一个[列表](https://wiki.openwrt.org/toh/start)，直接参照这个列表选就可以了。
2.  有电源/usb供电：在寝室使用的话因为有段时间断电但不断网，所以需要自带电源或可用移动电源usb供电。
3.  性价比高：因为只用于转发校园网，所以可以买便宜一些的。

最终选择了`TP-Link mr12u`这款路由器，在闲鱼上找了一家同城二手的，45元人民币拿下。

<!--more-->

**注意下面需要在`linux`终端环境下操作**

## 刷不死Boot

由于路由器固件的特殊性，一旦刷崩了或者设置错误导致无法正常登陆路由器，那么就无法对路由器进行管理，也就是所谓的变砖。

不死boot的作用就是在这种情况下提供进路由设置重新刷固件的机会。

### 刷解锁固件

由于`U-Boot`分区默认是锁定的，所以无法刷入新的`boot`。因此我们要先刷入一个修改过的解锁`U-Boot`分区的固件，这个修改过的固件可以在[百度网盘下载](https://pan.baidu.com/s/1slWHygP)，另外由于我手上的这个是v1版本的，与v2版本的硬件不同，所以需要使用的是`mr11u-v2`的解锁固件（即`openwr-ar71xx-generic-tl-mr11u-v2-squashfs-factory.bin`）。下载完以后先长按复位键复位路由器，连接上以后直接进入`192.168.1.1` `TP-Link`默认的管理界面，在下图这里选择刚下好的固件刷入即可：

![](/images/mr11u-1.png)

（图源网络）

### 刷不死boot

先下载不死`boot`：

>   http://viseator.com/file/breed-ar9331-mr12u.bin

路由器自动重启以后使用网线连接电脑与路由器，先用浏览器登陆`192.168.1.1`，用户名为`root`密码为空，然后设置`ssh`密码并保存。

现在就可以使用`ssh`用`root`与刚刚设置的密码登陆路由器了：

```bash
ssh root@192.168.1.1
```

登陆以后先查看并记下`mac`地址，之后要用到：

```bash
ifconfig eth0
```

![](/images/mr12u-2.png)

[图片来源](http://xzper.com/2015/07/11/TP-MR12U%E5%88%B7openwrt-%E4%B8%8D%E6%AD%BBboot/)

然后`exit`退出`ssh`，使用`scp`命令传送下载好的`boot`包：

```bash
scp breed-ar9331-mr12u.bin root@192.168.1.1:/tmp/
```

再次登陆路由器，刷入`U-Boot`：

```
ssh root@192.168.1.1
cd /tmp
mtd write breed-ar9331-mr12u.bin u-boot
```

等待命令返回后直接将路由器关机。

想要进入不死`boot`，只需按住`reset`复位键不放，再开机，等待个十几秒后松开，再有线连接电脑与路由器，浏览器输入`192.168.1.1`就可以进入管理界面了，以后变砖了只要这样都可以重新刷固件，所以称不死。

进入不死`boot`以后，先进入下图界面设置之前记录的`mac`地址：

![](/images/mr12u-3.png)

[图片来源](http://xzper.com/2015/07/11/TP-MR12U%E5%88%B7openwrt-%E4%B8%8D%E6%AD%BBboot/)

## 刷入最新固件（可选）

下面就可以直接在不死`boot`里面选择固件更新刷入最新的固件了，最新固件的下载可以到[这里](https://downloads.openwrt.org/snapshots/trunk/ar71xx/generic/)找到。

但是`mr12u`的闪存只有可怜的4m，如果安装最新的`openwrt`就没有空间放下`mentohust`了，所以还不如就直接用这个解锁用的固件。

## 交叉编译mentohust

在网上找了一圈愣是没找到`ar71xx`处理器已经编译好的`mentohust`，只能选择自己交叉编译了。没有条件自己编译的可以使用我编译好的**只适用于ar71xx**处理器的`mentohust`: http://www.viseator.com/file/mentohust 。

### 依赖包的安装

可以到https://wiki.openwrt.org/zh-cn/doc/howto/buildroot.exigence 根据自己的发行版安装必要的软件包。

### 下载编译工具链

首先到https://downloads.openwrt.org/snapshots/trunk/ar71xx/generic/ 页面下载 [OpenWrt-SDK-ar71xx-generic_gcc-5.3.0_musl-1.1.16.Linux-x86_64.tar.bz2](https://downloads.openwrt.org/snapshots/trunk/ar71xx/generic/OpenWrt-SDK-ar71xx-generic_gcc-5.3.0_musl-1.1.16.Linux-x86_64.tar.bz2) 处理器`SDK`，解压后进入目录下的`./staging_dir/toolchain-mips_34kc_gcc-5.3.0_musl-1.1.16/bin`。

### 配置环境变量

```bash
export PATH=$PATH:到上述/staging_dir/toolchain-mips_34kc_gcc-5.3.0_musl-1.1.16/bin 目录的完整路径
export CC=mipsel-openwrt-linux-gcc  
export CPP=mipsel-openwrt-linux-cpp  
export GCC=mipsel-openwrt-linux-gcc  
export CXX=mipsel-openwrt-linux-g++  
export RANLIB=mipsel-openwrt-linux-uclibc-ranlib
export LDFLAGS="-static"  
export CFLAGS="-Os -s"  
```

### 编译libpcap动态链接库

到 http://www.tcpdump.org/ 下载[libpcap-1.8.1.tar.gz](http://www.tcpdump.org/release/libpcap-1.8.1.tar.gz)，解压以后进入目录，执行：

```bash
./configure --host=mipsel-openwrt-linux --prefix=自已设定路径/ --with-pcap=linux
```

然后执行：

```bash
make
```

会报错误，但是不影响我们需要的`libpcap.a`文件，在当前目录下找到这个文件复制出来备用。

### 编译mentohust

克隆`mentohust`源码：

```bash
git clone https://github.com/hyrathb/mentohust
```

进入目录，首先生成`configure`：

```bash
sh autogen.sh
```

然后配置：

```bash
./configure --host=mipsel-openwrt-linux   --disable-encodepass --disable-notify --prefix=自设目录 --with-pcap=前面保存的libpcap.a文件路径
```

编译：

```bash
make
```

成功以后就可以在`src`目录下找到编译好的`mentohust`文件了。

## 部署

我们把编译好的文件传送到路由器中：

```bash
scp mentohust root@192.168.1.1:/root
```

### 安装libpcap

路由器中默认没有我们依赖的`libpcap`库，我们要手动安装，先下载：

>   http://www.viseator.com/file/libpcap_1.0.0-2_ar71xx.ipk

然后传送到路由器中：

```bash
scp libpcap_1.0.0-2_ar71xx.ipk root@192.168.1.1:/tmp
```

下面登陆路由器，进入`/tmp`目录，执行：

```bash
opkg install libpcap_1.0.0-2_ar71xx.ipk
```

### 新建wifi与桥接配置

新刷的路由器只有一个默认接入点，我们先到路由器管理界面修改接入点。增加访问密码等等。这一步的配置就不多说了网上都有。

由于这个路由器只有一个接口，我们现在是将它作为`lan`口在用的，但是实际上我们需要使用它作为`wan`口来连接校园网认证上网，并且要将`lan`口与`wifi`进行桥接使得我们依旧可以通过`192.168.1.1`这个地址来管理路由器。

这步操作需要直接修改`/etc/config/network`文件，如果使用图形界面配置可能会导致变砖。

我们登陆路由器以后直接用`vim`修改上述文件：

```bash
vim /etc/config/network
```

下面提供我找到的示例文件供参考：[出处](http://www.right.com.cn/forum/thread-105317-1-1.html)

```
config interface 'loopback'
        option ifname 'lo'
        option proto 'static'
        option ipaddr '127.0.0.1'
        option netmask '255.0.0.0'

config interface 'lan'
        option type 'bridge'
        option proto 'static'
        option ipaddr '192.168.1.1'
        option netmask '255.255.255.0'

config interface 'wan'
        option ifname 'eth0'
        option _orig_ifname 'eth0'
        option _orig_bridge 'false'
        option proto 'dhcp'
        option macaddr 'xx:xx:xx:xx:xx:xx'替换为自己的mac
```

修改后保存，然后`reboot`重启。

现在就不能通过有线来管理路由器了，因为管理地址已经桥接到了无线上了。所以我们要使用无线连接，有线接校园网，然后登陆到路由器。

找到我们存放`mentohust`的`/root`目录（默认就是），启动`mentohust`:

```bash
./mentohust -u username -p password -n eth0
```

如果要后台运行加个`-b1`就可以了。

如果一切正常的话现在无线就可以正常上网了。
