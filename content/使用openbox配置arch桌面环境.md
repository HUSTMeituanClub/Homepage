Title: 使用openbox配置archlinux桌面环境w
Date: 2017-05-18 04:37
Tags: linux, desktop environment, openbox
Authors: Huatian Zhou
Category: Linux

<h2>0x01 前言</h2>
<p>试用了一些 <code>archlinux wiki</code> 上推荐的桌面环境，发现并没有什么我喜欢的。</p>
<p>所以决定自己用 <code>openbox</code> 配置一发w。</p>
<h2>0x02 安装openbox并设置为默认桌面环境</h2>
<p>安装很简单， <code>pacman</code> 一下就好了。</p>
<p>如果你像我一样，在 <code>/etc/X11/xinit/xinitrc</code> 下面配置好了执行 <code>~/.xinitrc</code> ，那么以下操作就直接编辑 <code>~/.xinitrc</code> 就好了。</p>
<p>如果不是，那么可以在 <code>/etc/X11/xinit/xinitrc</code> 里写。</p>
<p>&nbsp;</p>
<p>首先建立 <code>/usr/local/bin/mydesk</code> ，然后在里面加入：</p>
<pre><code class="shell"><br />#!/bin/sh

openbox

</code></pre>
<p>&nbsp;</p>
<p>然后编辑 <code>xinitrc</code> ，把原来的桌面环境注释掉，换成</p>
<pre><code class="shell"><br />exec /usr/local/bin/mydesk

</code></pre>
<p>&nbsp;</p>
<p>这样下次启动 <code>X</code> 的时候，就会启动 <code>Openbox</code> 了。</p>
<p>&nbsp;</p>
<h2>0x03 安装其他辅助工具</h2>
<p>如果只安装 <code>Openbox</code> 的话，桌面上空空如也，连启动程序都不太容易。</p>
<p>自然会想到需要一些辅助用的程序。</p>
<p>首先，建议安装 <code>Docky</code> 。安装方法也很简单，直接 <code>pacman -S docky</code> 就可以了。</p>
<p>要让它开机启动的话，编辑 <code>/usr/local/bin/mydesk</code> ，在 <code>openbox</code> 这一行前面加入</p>
<p><code> sh ~/.mydesk.conf/.autostart</code></p>
<p>然后建立 <code>~/.mydesk.conf/.autostart</code> 文件，然后在里面添加：</p>
<pre><code class="shell"><br />#!/bin/sh

docky &amp;

</code></pre>
<p>就可以开机启动 <code>docky</code> 了。</p>
<p>桌面背景黑漆漆的是不是很难看？试试 <code>feh</code> 吧。直接 <code>pacman</code> 就可以安装。</p>
<p>在 <code>.autostart</code> 里加入：</p>
<p><code> feh --bg-fill /path/to/your/background/file.jpg</code></p>
<p>就可以设置桌面背景了。</p>
<p>还想要更多？试试桌面特效 <code>compton</code> 如何？同样是直接 <code>pacman</code> 就可以安装了。</p>
<p>启动的方法是在 <code>.autostart</code> 里加入：</p>
<p><code> compton --config ~/.compton.conf &amp;</code></p>
<p>配置 <code>compton</code> 的方法请自行 <code>google</code> w！</p>
<p>这样，基本的桌面环境就已经可以使用了！</p>
<p>但是有人会问：怎么没有 <code>widget</code> 啊？都没办法好好连 <code>wifi</code> 了w！</p>
<p>嗯……如果可以接受命令行的话，不妨试试 <code>wifi_menu</code> 或者给 <code>wpa_supplicant</code> 加 <code>alias</code> w！</p>
<p>当然了，我们要优雅的GUI！</p>
<p>安装 <code>tint2</code> ！这东西可以在你的屏幕上方显示一行任务栏一样的东西w！</p>
<p>同样需要在 <code>.autostart</code> 里加入 <code>tint2 &amp;</code> 来启动哦！</p>
<p>网络 <code>widget</code> 的话，可以使用 <code>nm-applet</code> w！</p>
<p>对了对了，还有输入法和锁定屏幕……</p>
<p>输入法的话 直接在 <code>.autostart</code> 里加入 <code>fcitx &amp;</code> 就可以使用输入法了！</p>
<p>锁定屏幕，可以去试试 <code>i3lock</code> ，配置教程应该可以在 <code>archlinux wiki</code> 上找到。</p>
<p>之后就是编辑 <code>~/.config/openbox/rc.xml</code> 增加锁定快捷键了。</p>
<p>&nbsp;</p>
<h2>0x04 笔记本电脑？</h2>
<p>也没有什么特别好说的辣w</p>
<p>就是一个电池状态 <code>widget</code> 的事情w</p>
<p><code>archlinux wiki</code> 上说的 <code>batterymon</code> 在 <code>AUR</code> 上找不到了w</p>
<p>但是有一个 <code>batterymon-clone</code> 。</p>
<p>直接在 <code>AUR</code> 上安装就好了！</p>
