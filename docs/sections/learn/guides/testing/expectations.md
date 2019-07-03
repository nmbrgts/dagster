## Data Quality Tests 

One of the reasons why traditional software engineering techniques do not apply to data pipelining is because the data pipeline authors do not control the incoming data. One might say that traditional application developers do not control their input, because they do not control their users. However this analogy is flawed. If a user presents invalid input to an application, the developer can simply refuse to do the computation, report an error to the user, and have her re-enter the data.
 
This is not possible for a data pipeline author. They are taking input from systems or previous data pipelining step that they do not control. If unexpected inputs appear that breaks the computation, the developer must update the upstream data source somehow – which is often impossible – or update the computation to adjust to the unexpected input – which is what almost always happens. Software abstractions and techniques in data pipelining must account for this unfortunate reality.
 
Testing the code of a data pipeline is necessary but not sufficient to ensure that a data pipeline works and reliable. You must also monitor your pipeline. Monitoring traditionally has meant that you monitoring the operational aspects of a pipeline or system – e.g. monitoring resource consumption, error rates, and so forth. However this is also insufficient to the task.
 
Because, as described above, data pipeline authors do not control their incoming data, there are a number of assumptions baked into the code they have written in terms of the shape and nature of that data. It is critical that the pipeline author move those assumptions from being implicit to explicit. 

When data computations are built, their authors are expected to sample and view data at a given instant in time, and then that computation is expected to operate in perpetuity on all the data that will ever come. That at minimum difficult and oftentimes impossible.
 
Data quality tests that explicitly encode the assumptions of a data pipeline author are critical to the health of a well-functioning data application. Broken assumptions should be detected as early as possible and as clearly as possible. They should be executed whenever data passes through the system, and then actions – e.g. emitting a message to a monitoring system, or halting the computation. Ideally these actions are taken based on some sort of policy engine driven by configuration.