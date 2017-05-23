Title: MacTex配置中文&fontawesome
Date: 2017-05-23 08:40:57
Tags: xelatex, 配置, OS X
Authors: Weihong Wang
Category: latex

最近报名了一个hackinit()的活动，然后需要写一份简历，去github上捞了一波模版，然而对于一个从来没用过latex的小白来说，刚开始的时候最麻烦的怕不就是本地环境的搭建了w

捞的resume模版[在这里！](https://github.com/dyinnz/uniquecv)，是联创前队长写的一份uniquecv。

下面开始配置：

### 安装MacTex

听很多人说这个软件是mac下比较好用的latex工具，所以就下载了，对于没接触过latex的小白来说，直接点击下载那个完整版，就是2.7G的那个文件

[这里是下载链接](http://www.tug.org/mactex/downloading.html)

#### 打开以后会得到一大堆的东西
<img src="/images/mactax.jpg">


### 打开taxshop
之后的编译等等都是在这个软件下进行的。具体的latex语法什么的就不细说了。

### 配置中文
1. 左上角将latex选为xelatex

   ![更改xelatex](/images/xelatex.jpg)

2. 打开texshop的「偏好设置」将「字符编码」改为`utf-8`，记得保存文件的时候也看一下是否是以`utf-8`编码的哦w

3. 前往系统的「应用软件」->「字体集」，查看你需要的是什么字体。
  如图上所示：Songti SC

  ![Songtisc](/images/songtisc.jpg)

4. 测试一下w：
```latex
\documentclass[nofonts]{ctexart}
\setCJKmainfont[BoldFont=STHeiti, ItalicFont=STKaiti]{STSong}
\setCJKsansfont[BoldFont=STHeiti]{STXihei}
\setCJKmonofont{STFangsong}
\begin{document}
汉字ddd
\end{document}
```

此时应该就可以显示出中文啦

![zhongwen.jpg](/images/zhongwen.jpg)

### 配置fontawesome
> fontawesome是什么？

Font Awesome为您提供可缩放的矢量图标，您可以使用CSS所提供的所有特性对它们进行更改，包括：大小、颜色、阴影或者其它任何支持的效果。

这个也是一样的，去[fontawesome官网](http://fontawesome.io/)下载fontawesome压缩包

![fontawesome](/images/fontawesome.jpg)

之后就可以愉快地使用这个uniquecv啦hhhhh，反正我就这样配，然后搞定了，虽然搞了两节课orz。

测试一下：

```latex
\documentclass{uniquecv}
\usepackage{fontawesome}
\begin{document}
\name{名字}
\medskip
\basicinfo{
  \faPhone ~ (+86) 153-0000-8888
  \textperiodcentered\
  \faEnvelope ~ username@email.com
  \textperiodcentered\
  \faGithub ~ github.com/username
}

\section{教育背景}
\dateditem{\textbf{华中科技大学} \quad 软件工程 \quad 本科}{2014年 -- 2018年}
成绩：年级前100\% \quad 英语：CET6

\section{专业技能}
\smallskip
C/C++、Lisp、Java、算法与数据结构、Linux、Storm、Hadoop、Spark、Flink、Hive、Hbase

\section{获奖情况}
\datedaward{一等奖}{XYZ应用开发大赛} {2026年06月}
\datedaward{\small{这是一个比较长长长长的奖}}{比较长的奖的比赛}{2016年04月}
\datedaward{冠军}{武汉KK编程挑战赛} {2015年09月}
\medskip


\section{项目经历}


\datedproject{分布式流体计算项目}{竞赛项目}{2016年05月 -- 2016年06月}
\textit{性能优化、并行计算}
\vspace{0.4ex}

将一个单机的流体计算程序移植到多机平台
\begin{itemize}
  \item 计算节点内部使用OpenMP并行化
  \item 计算节点间使用MPI并行化
  \item 单机优化性能达2x, 多机接近线性加速比
\end{itemize}


\datedproject{这是一个测试项目}{导师项目}{2016年02月 -- 2016年04月}
\textit{编译技术、C++}
\vspace{0.4ex}

这是一个没有分点陈述的项目，如果没有分点陈述，LaTeX的排版会是什么样子？
这是一个没有分点陈述的项目，如果没有分点陈述，LaTeX的排版会是什么样子？
这是一个没有分点陈述的项目，如果没有分点陈述，LaTeX的排版会是什么样子？
这是一个没有分点陈述的项目，如果没有分点陈述，LaTeX的排版会是什么样子？


\datedproject{C-Compiler}{个人项目}{2016年02月 -- 2016年04月}
\textit{编译技术、C++}
\vspace{0.4ex}

使用C++实现了一个简单C语言编译器，支持生成到目标代码。
\begin{itemize}
  \item 支持C11标准大部分标准
  \item 实现了类似lex/flex的词法解析器生成工具
  \item 实现了类似yacc/bison的语法解析器生成工具
  \item 后端部分采用窥孔优化
\end{itemize}



\section{课外}
\dateditem{\textbf{华中科技大学XX团队}}{2016年06月 -- 至今}

\end{document}
```

最终效果如图：

![resumedemo](/images/resumedemo.jpg)


### 嘻嘻
这样就结束啦，毕竟mactex真的是对小白非常友好，目前就这样就可以啦w

### 后记
咦，虽然最后是写好了自己的简历，但是这份简历真的是简陋的可以，之后还是继续慢慢充实一下自己吧w
