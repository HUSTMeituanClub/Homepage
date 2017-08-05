Title: MapReduce：大规模集群上的简单数据处理方式 && MIT 6.824 Lab 1
Date: 2017-06-12 11:36:28
Tags: 分布式, lab
Authors: Lichen Zhang
Category: 分布式


MapReduce是Google公司的Jeffrey和Sanjay提出的一个编程模型，主要用于大规模数据集的并行运算。它吸收了函数式编程语言中的Map和Reduce，通过Map处理原始键值对生成中间键值对，通过Reduce合并相同中间键对应的值。这一特性符合很多现实生活中的场景。

这种编程模型下的程序可以并行化地在大规模集群上运行，而在这一过程中用户却不需考虑输入数据的划分、程序的运行安排、节点故障和机器间通信，只需完成对数据的处理和合并。

我阅读了MapReduce的论文，并完成了MIT 6.824的第一个Lab，对其有了更深的了解。

<!--more-->

## 过程总览

![overview](/images/Map-Reduce/overview.png)

1. 用户程序调用MapReduce库，先把输入文件划分为M份（M可由用户指定），每一份通常为16MB到64MB，如图左方所示分成了split0~4，然后将用户程序fork到集群内其它机器上。 
2. 用户程序副本中有一个称为master，其余称为worker，master负责调度，为空闲worker分配任务（Map任务或者Reduce任务）。 
3. Map worker开始读取对应的输入数据，它们从输入数据中抽取出Key-Value Pair，每一个都作为参数传递给Map函数，Map函数产生的中间Key-Value Pair被缓存在内存中。 
4. 缓存在内存中的中间Key-Value Pair会被定期写入本地磁盘，而且被分为R个区（R可由用户指定），这些中间Key-Value Pair的位置会被通报给master，master负责将信息通报给Reduce worker。 
5. master通报Reduce worker它负责的分区的位置，当Reduce worker把所有它负责的中间数据都读过来后，先对它们进行排序，使得相同Key的数据聚集在一起。若内部排序无法满足要求，则使用外部排序。
6. Reduce worker遍历排序后的中间Key-Value Pair，对于每个唯一的Key，都将Key与关联的Value传递给Reduce函数，Reduce函数产生的输出会添加到对应分区的输出文件中。
7. 当所有的Map和Reduce作业都完成了，master唤醒用户程序，MapReduce函数返回。
8. MapReduce共产生R个输出文件（对应R个Reduce任务），用作分布式存储系统或其他分布式应用中。


## 容错机制

### Worker错误

当master定期发送的ping在某一时间段内没有到达某worker时，将该worker置为失效：

1. 若该worker任务为Map，则将该worker的所有任务置为空闲，并在分配任务时将其安排给其他的worker；当一个接替其任务的Map worker完成时，向所有Reduce worker发送通知，任何还未从失效worker读取数据的Reduce worker将从新worker读取数据；
2. 若该worker任务为Reduce，则将该worker的正在运行的任务置为空闲，并在分配任务时将其安排给其他的worker；已完成的任务不做调整。

### Master错误

由于只有一个master，因此在发生错误时会返回主程序，由客户端确认状态。

### 容错性保证

当用户提供的Map和Reduce操作对输入为确定函数时，分布式实现的输出与顺序输出保持一致，这种一致性是通过对Map和Reduce操作的输出进行原子提交来保证的，即依赖于文件系统的原子性操作。

当用户提供的Map和Reduce操作对输入为不确定函数时，MapReduce系统也提供了很弱的处理机制（不再赘述）。

## 优化技巧

### 存储位置

利用GFS，对数据产生多个备份，在调用任务时，尽量从本地读取数据，避免网络调用占用带宽，降低速度。

### 片段分配

为了保证速度和准确性，需要有效分配片段，通常限制M，使每一份为16MB到64MB，而R为worker机器数量的小倍数。

### 备用任务

当一个MapReduce将要完成的时候，master启用备用进程，来执行还在执行的任务，以减少落后worker造成的影响。

## Lab 解析

本Lab要求你补全一个基本完成的MapReduce程序，共有5个Part，其中Part I、II为Sequential MapReduce，Part III、IV为Sequential MapReduce，Part V为附加任务。程序整体难度不大，主要的难点在于熟悉Go语言。

### Part I: Map/Reduce input and output

要求实现两个模板化的函数`doMap`和`doReduce`，按照注释所给步骤以及论文相关步骤编写即可。

```go
func doMap(
   jobName string, 
   mapTaskNumber int, 
   inFile string,
   nReduce int, 
   mapF func(file string, contents string) []KeyValue,
) {
   inContent, err := ioutil.ReadFile(inFile)
   if err != nil {
      fmt.Fprintln(os.Stderr, err)
      return
   }
   keyValue := mapF(inFile, string(inContent))
   partitions := make([]*json.Encoder, nReduce, nReduce)
   for id := 0; id < nReduce; id++ {
      handler, err := os.OpenFile(reduceName(jobName, mapTaskNumber, id), os.O_CREATE|os.O_WRONLY, 0644)
      if err != nil {
         fmt.Fprintln(os.Stderr, err)
         return
      }
      defer handler.Close()
      partitions[id] = json.NewEncoder(handler)
   }
   for _, keyValueSingle := range keyValue {
      _ = partitions[ihash(keyValueSingle.Key)%nReduce].Encode(&keyValueSingle)
   }
}
```

```go
func doReduce(
   jobName string, 
   reduceTaskNumber int, 
   outFile string, 
   nMap int, 
   reduceF func(key string, values []string) string,
) {
   midContentBuf := bytes.NewBuffer(nil)
   for maps := 0; maps < nMap; maps++ {
      f, err := os.Open(reduceName(jobName, maps, reduceTaskNumber))
      if err != nil {
         fmt.Fprintln(os.Stderr, err)
         return
      }
      io.Copy(midContentBuf, f)
      f.Close()
   }
   decoder := json.NewDecoder(bytes.NewReader(midContentBuf.Bytes()))
   var kv KeyValue
   keyValueMap := make(map[string][]string)
   for {
      err := decoder.Decode(&kv)
      if err == io.EOF {
         break
      }
      keyValueMap[kv.Key] = append(keyValueMap[kv.Key], kv.Value)
   }
   keys := []string{}
   for keyValueSingle := range keyValueMap {
      keys = append(keys, keyValueSingle)
   }
   sort.Strings(keys)
   answerFileName := mergeName(jobName, reduceTaskNumber)
   answerFile, err := os.OpenFile(answerFileName, os.O_CREATE|os.O_WRONLY, 0644)
   defer answerFile.Close()
   if err != nil {
      fmt.Fprintln(os.Stderr, err)
      return
   }
   encoder := json.NewEncoder(answerFile)
   for _, key := range keys {
      encoder.Encode(KeyValue{key, reduceF(key, keyValueMap[key])})
   }
}
```

### Part II: Single-worker word count

要求实现wordcount，闭着眼睛乱写可以通过测试。

```go
func mapF(filename string, contents string) []mapreduce.KeyValue {
   keyValues := make([]mapreduce.KeyValue, 0, 0)
   f := func(c rune) bool {
      return !unicode.IsLetter(c)
   }
   fields := strings.FieldsFunc(contents, f)
   for _, each := range fields {
      keyValues = append(keyValues, mapreduce.KeyValue{each, ""})
   }
   return keyValues
}

func reduceF(key string, values []string) string {
   return strconv.Itoa(len(values))
}
```

### Part III: Distributing MapReduce tasks

要求实现给worker分配任务的`schedule`函数，worker地址是通过`registerChannel`获取的，在`schedule`中会启动n个`goroutine`，每个都从`registerChannel`中获取worker地址，然后进行`RPC`调用，成功后，再放回到`registerChannel`中。这里首次使用了`channel`和`goroutine`等Go语言的高级特性，需要好好学习。

### Part IV: Handling worker failures

在Part 3的基础上，要求实现worker的容错机制，这里只需要简单地不把无法到达的worker加入`registerChannel`中。

```go
func schedule(jobName string, mapFiles []string, nReduce int, phase jobPhase, registerChan chan string) {
   var ntasks int
   var n_other int // number of inputs (for reduce) or outputs (for map)
   switch phase {
   case mapPhase:
      ntasks = len(mapFiles)
      n_other = nReduce
   case reducePhase:
      ntasks = nReduce
      n_other = len(mapFiles)
   }

   fmt.Printf("Schedule: %v %v tasks (%d I/Os)\n", ntasks, phase, n_other)

   var waitGroup sync.WaitGroup
   for task := 0; task < ntasks; task++ {
      waitGroup.Add(1)
      worker := <-registerChan
      go func(id int, worker string) {
         defer waitGroup.Done()
         args := DoTaskArgs{jobName, mapFiles[id], phase, id, n_other}
         ok := call(worker, "Worker.DoTask", args, nil)
         if !ok {
            for !ok {
               worker := <-registerChan
               ok = call(worker, "Worker.DoTask", args, nil)
               if ok {
                  go func() {
                     registerChan <- worker
                  }()
                  break
               }
            }
         } else {
            go func() {
               registerChan <- worker
            }()
         }
      }(task, worker)
   }
   waitGroup.Wait()
}
```

### Part V: Inverted index generation (optional for extra credit)

要求实现一个倒排索引，难度不大。

```go
func mapF(document string, value string) (res []mapreduce.KeyValue) {
   keyValues := make([]mapreduce.KeyValue, 0, 0)
   f := func(c rune) bool {
      return !unicode.IsLetter(c)
   }
   fields := strings.FieldsFunc(value, f)
   sort.Strings(fields)
   for _, each := range fields {
      keyValues = append(keyValues, mapreduce.KeyValue{each, document})
   }
   return keyValues
}
func reduceF(key string, values []string) string {
   uniq := make(map[string]int)
   for _, value := range values {
      uniq[value] = 1
   }
   answer := strconv.Itoa(len(uniq))
   name := make([]string, 0, len(uniq))
   for key, _ := range uniq {
      name = append(name, key)
   }
   answer += " "
   sort.Strings(name)
   answer += strings.Join(name, ",")
   return answer
}
```
