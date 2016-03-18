# Network Rail Train Movements Listener

Receive message from the real-time Network Rail Train Movements API and push
each message to an Amazon Web Services (AWS) Simple Queue System (SQS) queue.

This allows this code to be incredibly stable and uninteresting, allowing us to
be pretty confident we're not missing messages.

The more "exciting" (error-prone) tasks of decoding, joining with other
databases etc can be done by a consumer of the queue, buying us some time to
fix decoders when they break without losing messages.


## Useful sites

[http://www.networkrail.co.uk/data-feeds/](http://www.networkrail.co.uk/data-feeds/)

[https://datafeeds.networkrail.co.uk/ntrod/myFeeds](https://datafeeds.networkrail.co.uk/ntrod/myFeeds)

[http://nrodwiki.rockshore.net/index.php/Main_Page](http://nrodwiki.rockshore.net/index.php/Main_Page)

## Train Movements API

Channel name (all): ``TRAIN_MVT_ALL_TOC``

*Messaging from the TRUST system, containing reports of train movements past
timetabled calling and passing points.*

Documentation: [http://nrodwiki.rockshore.net/index.php/Train_Movement](http://nrodwiki.rockshore.net/index.php/Train_Movement)
