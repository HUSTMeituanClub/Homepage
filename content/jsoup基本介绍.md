Title: jsoup基本应用介绍
Date: 2017-04-20 8:22
Tags: Jsoup
Authors: Zijie Han
Categories: Java


前些时间要做一个v2ex的第三方客户端，偶然发现了一个爬虫神器jsoup.运用jsoup对网站进行爬虫非常容易，仅需几行代码即可完成对整个网站的爬虫。

jsoup是的主要功能如下：

1.从一个url，文件或者字符串中解析HTML

2.使用DOM或者CSS选择器来查找、取出数据；

3.操作HTML元素、属性和文本。

&nbsp;

<a href="http://jsoup.org/">jsoup官网</a>进入官网下载jar.jsoup是基于开源协议MIT发布的。
如何对一个网站进行爬虫呢？我们v2ex网站首页为例。首先打开<a href="http://v2ex.com">v2ex官网</a>筛选我们需要的内容，现以v2ex的首页中的问答为例，检查该元素，发现所有的问答都在下的<tbody>中。其次，我们所需要的标题为`<a href="xxx">标题内容</a>`


这条文本语句当中，检查副标题，其存在于`&lt;a class="node" href="xxx"&gt;程序员&lt;/a&gt;`以及`&lt;strong&gt;xxx&lt;/strong&gt;`等标签中。现在我们找到了我们需要的内容及其标签，如何爬取这些文件呢？我们仅仅需要几行代码即可，这里我们在子线程中爬去，因为在主线程中爬取时可能会报错：



```java
 Runnable runnable = new Runnable() {
        @Override
        public void run() {
            String url = "https://www.v2ex.com/";//伪装成浏览器进行访问，因为有的网站可能禁止爬虫。
            Connection connection = Jsoup.connect(url);
            connection.header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64; rv:32.0) Gecko/    20100101 Firefox/32.0");//这里不用管，随便写
            Document document = null;
            try {
                document = connection.get();//下载整个页面，以doc保存
            } catch (IOException e) {
                e.printStackTrace();
            }

            Elements elements = document.select("tbody tr");//删选tbody tr的标签
            for (Element element : elements) {
                String title = element.getElementsByClass("item_title").text();//选出标题
                String urll = element.select("a").attr("href");//根据类别选取
                String vtitle = element.getElementsByClass("node").text();//根据class选取副标题中的“程序员”字样
                String aserandlast = element.getElementsByTag("strong").text();  //由于我们爬到的strong标签有两个，所我们还需要将字符串进行一次分割
                <span class="pl-smi">String</span> src <span class="pl-k">=</span> element<span class="pl-k">.</span>select(<span class="pl-s"><span class="pl-pds">"</span>img<span class="pl-pds">"</span></span>)<span class="pl-k">.</span>attr(<span class="pl-s"><span class="pl-pds">"</span>src<span class="pl-pds">"</span></span>);       //抓取图片链接
                String[] Array = convertStr(aserandlast);
                if(urll != "" && title !=""){
                Log.d(TAG, "大标题为： "+title+"链接为："+urll+"小标题为: "+vtitle+"  /1:"+Array[0]+"   /2:"+Array[1]);
                Title title1 = new Title(title, urll);
                titleList.add(title1);}<a href="http://115.159.151.84/wp-content/uploads/2017/04/FD1WUCWPF2PG5B.png"><img src="http://115.159.151.84/wp-content/uploads/2017/04/FD1WUCWPF2PG5B-1024x392.png" alt="" width="730" height="279" class="alignnone size-large wp-image-111" /></a>
            }

            handler.sendEmptyMessage(0);
        }
    };
    private static String[](String str){
        String[] strArray = null;
        strArray = str.split(" ");
        return strArray;
    }
```

运行结果附图。

<a href="http://115.159.151.84/wp-content/uploads/2017/04/FD1WUCWPF2PG5B.png"><img class="alignnone size-large wp-image-111" src="http://115.159.151.84/wp-content/uploads/2017/04/FD1WUCWPF2PG5B-1024x392.png" alt="" width="730" height="279" /></a>

jsoup在使用过程中还添加了多个过滤器来防止攻击：
<ol>
     <li>none()：只允许包含文本信息</li>
     <li>basic(): 只允许基本标签：a,b,blockqoute,br,captiion,code,cite等等</li>
     <li>basicWihtImages():允许基本标签、图片信息</li>
     <li>relaxed(): 允许更多标签如：h1,h2,h3.h4.tbody,td,thead,tr,u,ul等等</li>
</ol>
除代码所示的方法以外，jsoup还支持很多很强大的方法：
可利用jsoup下载form表单并进行模拟登陆，详情可参见[jsoup官方网站](jsoup.org)
