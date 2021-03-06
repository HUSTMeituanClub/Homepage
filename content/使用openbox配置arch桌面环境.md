Title: B树w
Date: 2017-09-12 16:04
Tags: 算法, 数据结构
Authors: Huatian Zhou
Category: 数据结构


> -- 请问你是如何做到心里没有一点点B数的？
>
> -- 不好意思，我有w



## 0x00 Overview

B树 ( `B-tree` ) 作为一种自平衡的树结构，同样在插入、删除、查找等操作上提供了对数级的时间复杂度。但与广泛应用于各种应用当中的红黑树不同，它虽然实现上较红黑树稍微复杂，但是由于优秀的数据访问特性（为一次性读写大块数据做了优化），所以被广泛地应用于数据库和文件系统的实现上。现有的现代硬盘文件系统（包括`NTFS` 、`Ext4` ）的底层结构使用的都是 `B-tree` 。



## 0x01 Structure

在B树中，一个非叶子节点拥有复数个键 ( `key` ) 和复数个子节点。其中能够拥有的最大子节点的个数是最大能够拥有的 `key` 的数量 +1 。同时，它现有的子节点的个数也是它现有的 `key` 的数量 +1 。举例来看：

```
+---------------+
| 2 | 4 |   |   |
+---+---+---+---+
|   |   |
..--+   |   +--..
| 1 |   |   | 5 |
..--+   |   +--..
+--..
| 3 |
+--..
```

在上面这个节点中，它最大能够拥有 `4` 个键，也就是说它最大能够拥有 `5` 个子节点。现在它拥有 `2` 个键，也就是说它现在拥有 `3` 个子节点。其中，在 `key = 2` 前面的这个子节点的所有 `key` 都 ` < 2 ` ，在 `key = 2` 和 `key = 4` 之间的这个子节点所有的 `key` 都 `> 2 && < 4` ，在 `key = 4` 后面的这个子节点所有的 `key` 都      `> 4` 。在增加和删除的过程中，节点会被合并或者拆分、旋转。其中旋转的操作各位读者可能之前在红黑树当中听到过，但是看起来并不直观，但是在红黑树的等价，`2-3-4 树` ，或者说 ` 3 阶 B-树` 中，旋转的操作是很自然的。并且由于它的“同一节点多键”的特性，它的平衡操作发生得没有其余的自平衡树那么频繁，因此适用于文件系统的底层结构。



## 0x02 Search

emmm... 查询并不需要细说w。请自行根据它的特点进行查找（当然是对数时间复杂度w



## 0x03 Insertion

![B-tree Insertion Example](https://upload.wikimedia.org/wikipedia/commons/3/33/B_tree_insertion_example.png "插入操作示例")

0. 所有的插入操作都必须从一个叶子节点开始。也就是说，我们必须找到一个没有子节点的节点，并且父节点符合将被插入的节点的要求。
1. 如果这个叶子节点还有空位（ `key` 数量未达到它的最大 `key` 数量），那么直接执行插入操作，树是平衡的。（示例中插入 值 4 ）
2. 如果这个叶子节点已经满了，那么：
3. 找到一个中间值，将其余值中比它小的放在它的左边，比它大的放在它的右边。
4. 将这个中间值插入父节点。（示例中插入 值 5）
5. 如果父节点已满，则继续拆分。在必要的情况下，更换根节点。（示例中插入 值 3 和 7）



## 0x04 Deletion

这是整个树操作中最困难的部分w..

很抱歉没有比较好的示意图w..

### 从叶子节点删除一个数据

0. 找到那个数据（
1. 如果那个数据在叶子节点，将它删除。
2. 如果删除之后，叶子节点小于它的 `key` 数量下限（不一定是 ` 0个`），那么进行平衡。



### 从非叶子节点删除一个数据

注意每一个B树的非叶子节点数据左右两边都有子树。那么：

0. 选择一个新的值（左子树的最大值或右子树的最小值，这样能够确保树的结构）。
1. 移除这个新值，并把将要删除的值替换为这个新值。
2. 这相当于从叶子节点删除了一个数据。按照从叶子节点删除数据的条件进行平衡。



### 平衡

- 如果需要被平衡的节点的右兄弟存在并且拥有比数量下限至少多一个的 `key` ，那么左旋 -- 

1. 将父节点的中间值旋转到被平衡节点中（父节点失去键-左子节点得到键）
2. 将右兄弟节点的最小值旋转到父节点的中间值（父节点得到键-右子节点失去键）
3. 树现在是平衡的。



- 如果需要被平衡的节点的左兄弟存在并且拥有比数量下限至少多一个的 `key` ，那么右旋 --

1. 将父节点的中间值旋转到被平衡节点中
2. 将左兄弟节点的最大值旋转到父节点的中间值
3. 树现在是平衡的。



- 如果两边的兄弟都不能给一个 `key` 给你，那么很抱歉w...

1. 如果你是最左边的叶子节点，那么找到父节点刚好在你右边的那个值。
2. 其它情况下，找到父节点刚好在你左边的那个值。
3. 以下将以找到的那个值为基准。
4. 将这个值移动到它左边的子节点。
5. 将这个值右边子节点的所有内容移动到左边的子节点。
6. 现在这个值的位置和右边子节点的位置都空了下来。删除它们。
7. 如果这个删除操作导致了这个值所在的节点的 `key` 数量少于数量下限，那么：
8. 如果这个节点是根节点且 `key` 数量等于 0 ，那么重新设置根节点，并将这个节点删除。
9. 否则，将这个节点设置为需要被平衡的节点，重复平衡操作。

