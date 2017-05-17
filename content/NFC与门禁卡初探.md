Title: NFC与门禁卡初探
Date: 2017-05-17 11:36:21
Tags: hack, NFC
Authors: Lichen Zhang
Category: NFC


# 前言

开学之后，学校寝室和启明学院都开始使用了以校园卡为载体的门禁服务，只有刷指定人员的校园卡才能进入。我对其原理产生了好奇，就趁机进行了一些研究。

# 了解NFC

NFC，near field communication(近场通信)，是一种短距离的高频无线通信技术，允许电子设备之间进行非接触式点对点数据传输，在十厘米内交换数据。2004年，诺基亚、飞利浦以及索尼三家公司建立了NFC forum，成为了NFC的开端。

NFC从其本质上来说，是一种RFID的演进技术，其于04年和05年发布了两个协议标准，分别是ISO/IEC 18092：2004和ISO/IEC 21481：2005。上述两个协议均源于更早的RFID协议 ISO/IEC 14443，即13.56MHz RFID协议标准。上述两个NFC协议推出的第二版分别是ISO/IEC 18092：2013(NFCIP-1)和ISO/IEC 21481：2012(NFCIP-2)。NFC向下兼容索尼的FeliCaTM标准以及飞利浦的MIFARE标准。

| 技术     | 协议                             | 频率                                       | 传输距离  | 主动   | 被动   | 典型设备和应用               |
| ------ | ------------------------------ | ---------------------------------------- | ----- | ---- | ---- | --------------------- |
| NFC    | ISO/IEC 18092<br>ISO/IEC 21481 | 13.56 MHz                                | 10 cm | √    | √    | 对等网络中的智能手机、平板电脑、便携式设备 |
| 免接触智能卡 | ISO/IEC 14443                  | 13.56 MHz                                | 10 cm |      | √    | 票务、支付、门禁、护照等          |
| RFID   | ISO/IEC 18000                  | LF (120–150 KHz)<br>HF (13.56 MHz)<br>UHF (433–900 MHz) | <40 m | √    | √    | 标记和跟踪物品，适用于制造物流、零售等   |

NFC的工作模式有三种，卡模拟模式（Card emulation mode）、点对点模式（P2P mode）和读/写模式（Reader/Writer mode）。

+ 在读/写模式中，NFC读/写器从NFC智能对象中读取数据，并根据这些信息操作。例如，采用支持NFC的手机，用户可以通过检索的URL自动联网、无需键入便可发送短信(SMS)文本、获取优惠券等，所有这些仅需触摸此对象的设备即可。
+ 在点对点模式中，任何支持NFC功能的读/写器都可与另一个NFC读/写器进行通信并交换数据，与读/写模式具有同样的安全性、直观性和简单性等优势。在这种模式下，一个读/写器可作为一个标签，创建通信链路。例如，具有读/写器的两个设备(如智能电话)可以彼此通信。
+ 卡模拟模式的NFC器件可以取代非接触式智能卡，使NFC器件能够用于现有的非接触式卡基础设施，进行票务、门禁、运输、收费站以及非接触式支付等操作。

# 复制流程

## 初步分析

由于采集门禁卡信息时，只需要提供学号和姓名，以及卡编号，无需其他信息，故推测门禁只是简单读取卡的ID，而不会去解密其他信息，只需要使用卡模拟模式，简单地模拟一个ID相同的卡即可。在网上查阅资料可得知，门禁卡的工作原理大多如此。

## 信息采集

由于手头设备有限，只能用手机查看校园卡的ID信息。

[NFC Tools下载地址](https://play.google.com/store/apps/details?id=com.wakdev.wdnfc)
![](/images/ID-information.jpg)

容易得到，Serial number处为形如`XX:XX:XX:XX`的ID（X为16进制数字）。这就是门禁所识别的ID。

## 信息查询

查阅相关资料可以得知，NFC的相应配置保存在`/system/etc/libnfc-nxp.conf`或`/system/etc/libnfc-brcm.conf`中，具体的配置取决于NFC芯片的类型。

手头有一部Nexus 6P，其芯片为NXP PN548，故阅读了`libnfc-nxp.conf`，通过注释从中发现了需要更改的配置。在文件的607行，有Core configuration settings中的`LA_NFCID1`，代表了手机NFC的NFCA-ID，这正是门禁系统能识别的ID。这里，33表示配置的类型，04表示后面所跟的配置字节数，后面的四个字节为数据。

```xml
###############################################################################
# Core configuration settings
# It includes
# 18        - Poll Mode NFC-F:   PF_BIT_RATE
# 21        - Poll Mode ISO-DEP: PI_BIT_RATE
# 28        - Poll Mode NFC-DEP: PN_NFC_DEP_SPEED
# 30        - Lis. Mode NFC-A:   LA_BIT_FRAME_SDD
# 31        - Lis. Mode NFC-A:   LA_PLATFORM_CONFIG
# 33        - Lis. Mode NFC-A:   LA_NFCID1
# 50        - Lis. Mode NFC-F:   LF_PROTOCOL_TYPE
# 54        - Lis. Mode NFC-F:   LF_CON_BITR_F
# 5B        - Lis. Mode ISO-DEP: LI_BIT_RATE
# 60        - Lis. Mode NFC-DEP: LN_WT
# 80        - Other Param.:      RF_FIELD_INFO
# 81        - Other Param.:      RF_NFCEE_ACTION
# 82        - Other Param.:      NFCDEP_OP
NXP_CORE_CONF={20, 02, 2B, 0D,
        18, 01, 01,
        21, 01, 00,
        28, 01, 00,
        30, 01, 08,
        31, 01, 03,
        33, 04, 00, 00, 00, 00,
        50, 01, 02,
        54, 01, 06,
        5B, 01, 00,
        60, 01, 0E,
        80, 01, 01,
        81, 01, 01,
        82, 01, 0E
}
```

## 信息修改

将上面获取到的ID插入配置文件中，重启手机NFC，即可完成修改。

```sh
 #!/system/bin/sh
 sed -i '607s/^.*$/        33, 04, XX, XX, XX, XX,/' /etc/libnfc-nxp.conf
```

## 批量修改

尝试着写了批量修改的脚本，以完成某些特殊要求，但是由于安卓系统本身的限制，无法做到自动重启NFC，贴代码仅供参考。

```sh
#!/system/bin/sh
setenforce 0
echo "SElinux disabled"
#disable SElinux
mount -o rw,remount /system
echo "nfc disabled"
service call nfc 5
sleep 1
#first person
sed -i '607s/^.*$/        33, 04, XX, XX, XX, XX,/' /etc/libnfc-nxp.conf
sleep 1
service call nfc 6
echo "nfc enabled"
sleep 5
service call nfc 5
echo "nfc disabled"
sleep 1
#second person
sed -i '607s/^.*$/        33, 04, XX, XX, XX, XX,/' /etc/libnfc-nxp.conf
service call nfc 6
echo "nfc enabled"
sleep 1
setenforce 1
```

# 总结

门禁使用易于复制的射频卡ID检测是极为不安全的，外来人员只需要注意到这一点就可以轻松地进入宿舍，同时，此功能还可以用来体育打卡、进入图书馆等，需要慎加利用。
