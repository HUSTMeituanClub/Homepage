Title: Android利用UDP、TCP进行局域网数据传输
Date: 2017-05-11 15:58:06
Categories: Android
Tags: Android, Network
Authors: Di Wu

## 写在前面

在团队内部的hackweek中实现了一个在局域网环境中（同一个wifi下）进行的卡片收发小游戏，踩了一些关于局域网内通信的坑，这篇博文就用来整理一下整个过程的思路，[完整代码地址](https://github.com/viseator/AnonymousCard)。

## 实现思路

在整个过程中利用到了UDP与TCP两种传输层协议，两者的特性决定了使用上的不同。

简单地说，UDP非面向连接，不需要先与目标建立连接，所以UDP不提供可靠的数据传输，也不能保证数据准确无误地到达目的地，但UDP的优势在于它可以迅速传送大量信息，传输性能比较好。

而TCP是面向连接的协议，需要经过三次握手与目的地址建立一个稳定的连接，可以保证数据准确、完整地到达。但是它的传输效率就没有UDP那么高。

首先，为了数据传输的稳定和准确性，在传送主要数据部分我们必需使用TCP来建立一个点对点的稳定的连接来传输主要数据。

<!--more-->
但是，为了建立一个TCP连接，请求的一方必须要知道被请求一方（下面简称服务方）的IP地址。而在局域网中，如果我们想要实现每个人连接局域网以后马上可以收发信息，由于每次加入时分配到的IP地址并不是固定的也无法提前得知，所以我们需要使用其他的办法先获取到服务方的IP地址。

这时就要利用到UDP协议的组播特性了，组播可以让设备都加入一个预设好的组，然后就可以向这个组中发送数据包，只要加入了这个组的设备都可以收到这个数据包。这样只要所有的设备都提前加入了同一个组，不需要互相知道IP地址就可以交换数据，那么我们应该如何利用这样的特性呢？

结合我们的实际需求，游戏过程是每个人可以向所有人发送一个只有标题的匿名卡片（这个过程就符合UDP组播的特性），如果感兴趣的人就可以点击收到的卡片来打开这个卡片查看具体内容（这个过程就需要我们建立TCP连接来传输数据）。

所以我们就有了思路，向所有人发送卡片的过程使用UDP进行组播，数据包中除了包含标题信息还要包含一个发送人的IP地址以及一个Mac地址作为ID（考虑到重新连接后地址发生改变的问题），当所有人收到这个卡片以后需要建立连接的时候就可以得到发送人的IP来进行TCP连接。

下面我们来实现这个过程。
## 具体实现

### 组播

我们定义一个`ComUtil`类来处理组播

#### 加入组

```java
public static final String CHARSET = "utf-8";
private static final String BROADCAST_IP = "224.0.1.2"; //IP协议中特殊IP地址，作为一个组，用来集合加入的所有客户端
public static final int BROADCAST_PORT = 7816; //广播目的端的端口号
private static final int DATA_LEN = 4096;
private MulticastSocket socket = null;
private InetAddress broadcastAddress = null;//当前设备在局域网下的IP地址
byte[] inBuff = new byte[DATA_LEN];
private DatagramPacket inPacket = new DatagramPacket(inBuff, inBuff.length);//用于接受对象的packet
private DatagramPacket outPacket = null;//用于发送对象的packet
private Handler handler;
public ComUtil(Handler handler) {
    this.handler = handler;//回调使用Handler机制
}
```

```java
public void startReceiveMsg() {
    try {
        socket = new MulticastSocket(BROADCAST_PORT);//打开一个组播Socket
        broadcastAddress = InetAddress.getByName(BROADCAST_IP);//需要进行一步转换来使用String类型的IP地址
        socket.joinGroup(broadcastAddress);//加入一个组
        outPacket = new DatagramPacket(new byte[0], 0, broadcastAddress, BROADCAST_PORT);//用于发送数据包的DatagramPacket
    } catch (IOException e) {
        e.printStackTrace();
    }
  //下面两行用于下文中的开始接收广播
    Thread thread = new Thread(new ReadBroad());
    thread.start();
}
```

注释应该讲得比较清楚了，这里要注意的是UDP数据的收发需要使用一个`DatagramPacket`来进行。可以理解为一个数据包。

#### 接收组播信息

上面的代码最后两行新建了一个线程用于接收组播信息，具体代码如下：

```java
class ReadBroad implements Runnable {
    public void run() {
        while (true) {
            try {
                socket.receive(inPacket);
                Message message = new Message();
                message.what = BROADCAST_PORT;
                message.obj = inBuff;
                handler.sendMessage(message);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}
```

进行了一个无限循环，进行到第5行时如果没有收到广播的`DatagramPacket`会一直处于阻塞状态，收到一个`DatagramPacket`后就会通过`Handler`来转发出去，在`Handler`所在线程来处理这个数据包。之后再进行循环不断地接收并处理数据包。

#### 发送组播信息

```java
public void broadCast(final byte[] msg) {
    Thread thread = new Thread(new Runnable() {
        @Override
        public void run() {
            try {
                outPacket.setData(msg); //数据来源为外部，类型是二进制数据
                socket.send(outPacket);//向组中发送该数据包
            }
            catch (IOException ex) {
                ex.printStackTrace();
                if (socket != null) {
                    socket.close();
                }
            }
        }
    });
    thread.start();
}
```

这个方法由外部调用，传入一个二进制数组数据通过`setData()`放在数据包中向组中的所有成员发送。成员通过上一节的接收方法接收到的就会是同样的数据包。

### 数据处理

建立了组播的工具，下一步就要建立一个数据对象来进行信息的交换。由于数据包中的数据只能是以字节码的形式存在，所以我们设计的数据对象一定要是可序列化的（也就是实现了`Serializable`接口的），再通过流工具进行转换。

```java
public class UDPDataPackage implements Serializable {
    private String ipAddress;
    private String macAddress;
    private String title;
    private String id;
  ...
}
```

在这个简单的JavaBean中只定义了四个简单数据。

我们将自己的信息设置后就可以通过如下方法转换成一个字节数组再通过上面的广播方法来发送：

```java
comUtil.broadCast(ConvertData.objectToByte(new UDPDataPackage(...))); //发送数据
```

```java
//通过流来进行的序列化
public static byte[] objectToByte(Object object) {
    ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
    ObjectOutputStream outputStream;
    try {
        outputStream = new ObjectOutputStream(byteArrayOutputStream);
        outputStream.writeObject(object);
    } catch (IOException e) {
        e.printStackTrace();
    }
    return byteArrayOutputStream.toByteArray();
}
```

同样的，在接收到数据以后可以反序列化来得到原对象：

```java
public static Object byteToObject(byte[] bytes) {
    ByteArrayInputStream byteInputStream = new ByteArrayInputStream(bytes);
    Object object = null;
    try {
        ObjectInputStream objectInputStream = new ObjectInputStream(byteInputStream);
        object = objectInputStream.readObject();
    } catch (IOException | ClassNotFoundException e) {
        e.printStackTrace();
    }
    return object;
}
```

这样，我们就可以从这个对象中获取想到的IP地址等信息了。

### 建立TCP连接传输数据

想要建立TCP连接，需要客户端与服务端两端的配合，我们现在已经获取到了需要建立连接的IP地址，下面我们要做的是与这个地址的服务端建立连接再传输数据。服务端需要一直运行来随时准备接受可能的请求。

由于我们同一个设备既要作为客户端，也要作为服务端，所以要编写两个类。

#### 服务端

```java
public void startServer(Handler handler) {
    this.handler = handler;//利用handler进行处理
    thread = new Thread(new RunServer());
    thread.start();//另开一个线程接收连接请求
}
```

```java
class RunServer implements Runnable {
    @Override
    public void run() {
        ServerSocket serverSocket = null;
        try {
            serverSocket = new ServerSocket();//初始化一个ServerSocket
            serverSocket.setReuseAddress(true);
            serverSocket.bind(new InetSocketAddress(SERVER_PORT));//与端口绑定
        } catch (IOException e) {
            e.printStackTrace();
        }
        while (true) {
            try {
                Socket socket = serverSocket.accept();//利用accept方法获得socket
                InputStream inputStream;
                inputStream = socket.getInputStream();//获取输入流（来源自客户端）
                ObjectInputStream objectInputStream = new ObjectInputStream(inputStream);//转换为对象输入流

                //获取udpDataPackage对象
                UDPDataPackage udpDataPackage = (UDPDataPackage) objectInputStream.readObject();
                OutputStream outputStream = socket.getOutputStream();
                ObjectOutputStream objectOutputStream = new ObjectOutputStream(outputStream);
                objectOutputStream.writeObject(udpDataPackage);//将数据包写入输出流传送给客户端
                objectOutputStream.flush();//刷新流

                objectOutputStream.close();
                outputStream.close();
                objectInputStream.close();
                inputStream.close();
            } catch (IOException | ClassNotFoundException e) {
                e.printStackTrace();
            }
        }
    }
}
```

解释见注释。

#### 客户端

```java
public void sendRequest(String ipAddress, UDPDataPackage udpDataPackage, Handler handler) {
    this.ipAddress = ipAddress;//即为之前获取到的IP地址
    this.udpDataPackage = udpDataPackage;
    this.handler = handler;
    thread = new Thread(new SendData());
    thread.start();
}
```

```java
class SendData implements Runnable {
    @Override
    public void run() {
        Socket socket = null;
        try {
            socket = new Socket(ipAddress, SERVER_PORT);//新建一个socket
            socket.setReuseAddress(true);
            socket.setKeepAlive(true);//设置socket属性
            socket.setSoTimeout(5000);//设置超时
			//获得一个对象输出流
            OutputStream outputStream = socket.getOutputStream();
            ObjectOutputStream objectOutputStream = new ObjectOutputStream(outputStream);
            objectOutputStream.writeObject(udpDataPackage);//将请求包写入输出流（传送给服务端）
			//获取服务端返回的流
            InputStream inputStream = socket.getInputStream();
            ObjectInputStream objectInputStream = new ObjectInputStream(inputStream);
            udpDataPackage dataPackage = (udpDataPackage) objectInputStream.readObject();//获取到返回的数据对象
			//转发给handler进行处理
            Message msg = new Message();
            msg.what = SERVER_PORT;
            msg.obj = dataPackage;
            handler.sendMessage(msg);
        } catch (SocketTimeoutException e) {
            try {
                if (socket != null) socket.close();
            } catch (IOException e1) {
                e1.printStackTrace();
            }
            sendRequest(ipAddress, udpDataPackage, handler);
        } catch (IOException | ClassNotFoundException e) {
            e.printStackTrace();
        }
    }
}
```

解释见注释。

---

可以看见TCP连接还是比较简单的，设置好`socket`并获取到输入输出流以后就可以把服务端当作本地流一样操作，具体的网络通信实现过程被隐藏了，有了流以后就可以进行所有能对流进行的操作了。到这里，我们要实现的局域网数据传输已经完成了。

