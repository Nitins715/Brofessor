# Operating Systems (OS)

> **Source**: [CodeKairo CS Notes](https://codekairo.com/notes/operating-systems)  
> **Overview**: Complete operating systems curriculum covering processes, threads, CPU scheduling algorithms, process synchronization, classic deadlocks, inter-process communication, paging, virtual memory, and file systems.

---

## Table of Modules

1. [Introduction to Operating Systems](#module-1-introduction-to-operating-systems)
2. [Processes and Threads](#module-2-processes-and-threads)
3. [CPU Scheduling Algorithms](#module-3-cpu-scheduling-algorithms)
4. [Process Synchronization](#module-4-process-synchronization)
5. [Classic Synchronization Problems](#module-5-classic-synchronization-problems)
6. [Deadlocks in Operating Systems](#module-6-deadlocks-in-operating-systems)
7. [Inter-Process Communication](#module-7-inter-process-communication)
8. [Memory Management](#module-8-memory-management)
9. [Virtual Memory and Demand Paging](#module-9-virtual-memory-and-demand-paging)
10. [Page Replacement Algorithms](#module-10-page-replacement-algorithms)
11. [Disk Scheduling Algorithms](#module-11-disk-scheduling-algorithms)
12. [File Systems](#module-12-file-systems)

---

## Module 1: Introduction to Operating Systems

*Original URL: https://codekairo.com/notes/operating-systems/introduction-to-operating-systems*

### Overview

Quick answer

### What is an operating system?

An operating system is the software that manages a computer's hardware and gives programs a safe, simpler interface to it. It shares the CPU, memory, storage and devices among programs, keeps them from interfering with each other, and offers services such as files and processes through system calls. Its core, the kernel, runs in a privileged CPU mode that ordinary programs cannot enter.

- What an operating system does
- Kernel mode and user mode
- System calls
- Types of operating systems
- Monolithic kernel vs microkernel
- Common mistakes
- Interview questions
- Common questions
- Test yourself

An operating system (OS) is the layer of software between the hardware and the programs you run. A program wants to say "open this file" or "give me more memory"; the hardware only understands disk sectors, page tables and device registers. The OS bridges that gap, and it also decides who gets the hardware when many programs want it at once. Every later topic in these notes, from scheduling to file systems, is one part of that job.

Programs run in user mode above the line and reach the hardware only through system calls; the kernel runs in kernel mode below it, with full control of the CPU, memory and devices. Libraries such as libc turn an ordinary call like printf into those system calls.

### What an operating system does

There are two classic ways to describe the OS, and an interviewer is happy with either.

- A resource manager. The CPU, memory, disks and network cards are shared. The OS decides which process runs next, how much memory each one gets and in what order disk requests are served, and it keeps one program from taking everything.
- An extended machine. The OS hides ugly hardware behind clean abstractions: a file instead of disk blocks, a process instead of raw CPU registers, an address space instead of physical RAM, a socket instead of a network card.

Its main functions follow from that:

When the machine powers on, firmware (BIOS or, on modern PCs, UEFI) runs first, finds a boot loader on the disk, and the boot loader loads the kernel into memory. The kernel sets up memory management and devices, then starts the first user process (on most Linux systems, systemd ), which starts everything else.

### Kernel mode and user mode

The kernel is the core of the OS that stays in memory and runs with full control of the hardware. Ordinary programs must not have that control, or a bug in one program could wipe the disk or read another program's memory. The CPU enforces the split with a mode bit :

- Kernel mode (supervisor mode, ring 0 on x86): every instruction is allowed.
- User mode (ring 3 on x86): privileged instructions are refused. These include direct I/O, changing the page tables, disabling interrupts, setting the timer and halting the CPU.

If a user program tries a privileged instruction, the CPU raises an exception and the kernel usually terminates the program. The only ways into kernel mode are:

- System calls , a deliberate trap instruction from a program.
- Interrupts , signals from hardware (a key pressed, a disk read finished, the timer ticking).
- Exceptions , errors the CPU detects while running an instruction (divide by zero, a page fault, an illegal instruction).

The timer interrupt matters most. The kernel programs a hardware timer before handing the CPU to a process; when it fires, control returns to the kernel even if the program is stuck in an infinite loop. That is what makes preemptive multitasking possible.

The process runs in user mode and drops into kernel mode 4 times, once for each way in: a system call it makes, an interrupt from a device, an exception its own instruction causes, and the timer — which is how the kernel takes the CPU back from any program.

### System calls

A system call is the interface through which a program asks the kernel for a service. Programmers rarely issue one directly; they call a library function ( printf , fopen , malloc ) that makes the call when it needs one.

```
#
include
<unistd.h>
int
main
(
void
)
{
const
char
msg
[
]
=
"hello\n"
;
write
(
1
,
msg
,
sizeof
msg
-
1
)
;
/* system call: write 6 bytes to file descriptor 1 (stdout) */
return
0
;
}
```

Here is that write on x86-64 Linux, step by step: the wrapper, the trap, the kernel's system call table , the handler's checks and the return.

main() calls write(1, msg, 6) to print "hello" and a newline. That is an ordinary function call into the C library: the CPU is still in user mode.

- main() calls write(1, msg, 6) to print "hello" and a newline. That is an ordinary function call into the C library: the CPU is still in user mode.
- The wrapper puts write's system call number, 1, in rax and the three arguments in rdi, rsi and rdx, then executes the syscall instruction — the trap.
- The CPU switches to kernel mode and jumps to the kernel's one fixed entry point, which uses rax as an index into the system call table: entry 1 is write.
- sys_write first checks the arguments — the buffer at 0x402010 must lie in the caller's own memory — then writes 6 bytes to file descriptor 1, the terminal.
- The result, 6 bytes written, goes back in rax; the return instruction switches the CPU to user mode, and the wrapper returns 6 to main(). On failure it would return −1 and set errno.

Arguments travel in registers, in a block of memory whose address is passed in a register, or on the stack. A system call costs a mode switch , which is much cheaper than a full context switch to another process.

System calls are grouped into six categories:

### Types of operating systems

Operating systems grew in stages, and each stage fixed a weakness of the one before. Interviewers ask for these as definitions.

- Batch OS. Jobs with similar needs were collected and run one after another without user interaction. The CPU sat idle whenever a job waited for slow I/O.
- Multiprogramming OS. Several jobs are kept in memory at once. When the running job waits for I/O, the OS switches the CPU to another job. The goal is CPU utilization ; there is still no interaction.
- Multitasking or time-sharing OS. Multiprogramming plus a timer: each process gets a short time slice (a few milliseconds) and is then preempted, so many users or programs each get quick responses. The goal is response time . Unix, Linux, Windows and macOS are all time-sharing systems.
- Real-time OS (RTOS). Correctness depends on meeting deadlines. In a hard real-time system a missed deadline is a failure (airbag control, pacemakers, industrial controllers); in a soft real-time system it only lowers quality (a dropped video frame). Examples: FreeRTOS, VxWorks, QNX.
- Distributed OS. Several networked computers are managed so that users see one system: resources, files and computation are shared across machines. Research systems such as Amoeba explored it; today the idea mostly lives in cluster software rather than in an OS you install.
- Multiprocessor OS. One machine with several CPUs or cores sharing memory. In symmetric multiprocessing (SMP) , which every modern desktop OS uses, every core runs the kernel and schedules its own work.

The first three stages, run on the same two jobs:

Batch leaves the CPU idle whenever the running job waits for I/O: busy 67% of the time. Multiprogramming gives the CPU to B while A waits: 91%. Time-sharing also preempts every 2 units, so B first runs at 2 instead of 3 — a quicker response.

### Monolithic kernel vs microkernel

How much code runs in kernel mode is a design choice.

A monolithic kernel puts the scheduler, memory manager, file systems, network stack and device drivers in one program running in kernel mode, in one address space. Components call each other as ordinary functions, so it is fast. The cost is that a bug in any driver can crash or compromise the whole system. Linux and the BSDs are monolithic; Linux softens the rigidity with loadable kernel modules , so a driver can be added at run time.

A microkernel keeps only the minimum in kernel mode: address spaces, thread scheduling and inter-process communication (IPC) . File systems, drivers and the network stack run as separate user-mode server processes that talk by messages. A crashed driver can be restarted without a reboot, and the small kernel is easier to verify (seL4 has a formal proof of correctness). The cost is the extra message passing and mode switches on every service request. MINIX 3, QNX and seL4 are microkernels.

A monolithic kernel runs the file system and drivers in kernel mode beside the scheduler. A read() is one system call: in, then out — 2 mode switches — and inside the kernel the file system calls the driver as an ordinary function.

- A monolithic kernel runs the file system and drivers in kernel mode beside the scheduler. A read() is one system call: in, then out — 2 mode switches — and inside the kernel the file system calls the driver as an ordinary function.
- A microkernel moves the file system, drivers and network stack out into user-mode servers and keeps only scheduling, memory and IPC. The same read() becomes messages through the kernel: 8 mode switches, the price paid for a driver crash that no longer brings the system down.

Most mainstream systems sit between: Windows NT and macOS (XNU, built from the Mach microkernel and BSD code) are usually called hybrid kernels, with a microkernel-like structure but most services still in kernel mode for speed.

### Common mistakes

- Calling the kernel "the operating system": the kernel is one part of it; the shell, libraries and utilities are the rest.
- Saying printf is a system call. It is a library function; the system call it eventually makes is write .
- Treating a system call as a context switch. It is a mode switch inside the same process; a context switch changes which process runs.
- Mixing up multiprogramming and multitasking: only multitasking preempts on a timer.
- Calling any fast system "real-time". Real-time means deadlines are guaranteed, not that the system is quick on average.
- Saying a microkernel is always better. It trades speed for isolation, which is why most desktop kernels are monolithic or hybrid.

### Interview questions

What is the difference between kernel mode and user mode? In kernel mode the CPU executes every instruction, including privileged ones such as I/O and changing page tables. In user mode those are refused, so a program can only reach the hardware by asking the kernel through a system call. A mode bit in the CPU records which mode is active.

What happens when a program makes a system call? The library wrapper places the call number and arguments in registers and executes a trap instruction. The CPU switches to kernel mode, the kernel dispatches through its system call table, checks the arguments and does the work. It then returns the result and switches back to user mode.

What is the difference between an interrupt, a trap and an exception? An interrupt comes from hardware and is asynchronous to the running program, such as a disk finishing a read. A trap is a deliberate, synchronous entry into the kernel, such as a system call. An exception is a synchronous error caught by the CPU, such as division by zero or a page fault; some books group traps and exceptions together.

Why is the timer interrupt important? It guarantees the kernel regains the CPU periodically, even from a program in an infinite loop. Without it a process could keep the CPU forever, and preemptive scheduling would be impossible.

What are privileged instructions? Give examples. Instructions that may only run in kernel mode because misuse would break protection: starting I/O directly, loading the page table base register, disabling interrupts, setting the timer and halting the CPU. Reading the clock or adding two numbers is not privileged.

What is a hybrid kernel? A kernel structured like a microkernel, with separate subsystems and message-style interfaces, but with most services kept in kernel mode for performance. Windows NT and macOS's XNU are the usual examples.

What is the role of the boot loader? Firmware cannot load a large kernel by itself, so it runs a small boot loader (such as GRUB) from the disk. The boot loader loads the kernel image into memory and jumps to it; the kernel then starts the first user process.

Next, read Processes and Threads , or check yourself with the Operating Systems (Basic) skill test .

### What is the difference between an operating system and a kernel?

The kernel is the part of the operating system that runs in privileged mode and manages the CPU, memory and devices directly. The operating system is the kernel plus everything shipped around it: system libraries, the shell, utilities, services and often a graphical interface. Linux on its own is a kernel; Ubuntu or Android is an operating system built on it.

### Why do we need an operating system?

Without one, every program would have to drive the disk, screen and network itself and would trust every other program not to overwrite its memory. The operating system does that work once, shares the hardware fairly among many programs, and protects them from each other and the hardware from them.

### What is a system call in simple words?

A system call is a request from a program to the kernel for something only the kernel may do, such as reading a file, creating a process or sending data on a socket. The program executes a special trap instruction, the CPU switches to kernel mode, the kernel does the work, and control returns to the program in user mode.

### What are the main functions of an operating system?

Process management (creating, scheduling and ending programs), memory management (giving each process its own address space), file management, device and I/O management, protection and security, and networking. Most systems also provide a user interface, either a command shell or a graphical desktop, though that part runs outside the kernel.

### Is Linux a monolithic kernel or a microkernel?

Linux is a monolithic kernel: the scheduler, memory manager, file systems, network stack and device drivers all run together in kernel mode in one address space. It is modular, though, because drivers and file systems can be loaded and unloaded at run time as kernel modules, without rebooting.

### What is the difference between multiprogramming and multitasking?

Multiprogramming keeps several programs in memory and switches the CPU to another one when the running program waits for I/O, so the CPU is kept busy. Multitasking, or time-sharing, also switches on a timer every few milliseconds, so many interactive users or programs each get quick responses. Multitasking is multiprogramming with preemption added.


---

## Module 2: Processes and Threads

*Original URL: https://codekairo.com/notes/operating-systems/processes-and-threads*

### Overview

Quick answer

### What is the difference between a process and a thread?

A process is a program in execution with its own address space, open files and resources. A thread is a single path of execution inside a process; threads of the same process share its code, data, heap and open files but each has its own program counter, registers and stack. Creating and switching threads is therefore cheaper than for processes, but a bug in one thread can corrupt the others.

- What a process is
- The process control block
- Process states
- Context switch
- Creating processes: fork() and exec()
- Threads
- Process vs thread
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A process is a program in execution: the code plus everything that changes while it runs. A thread is one flow of execution inside a process. Every program you start becomes at least one process with one thread, and the operating system's job of "running many programs at once" is really the job of creating, switching and ending processes and threads. This note covers what the kernel keeps about each, how it moves between them, and why threads exist at all.

### What a process is

A program is a passive file on disk; a process is that program loaded into memory and running. One program can be several processes at the same time, each with its own state.

Each process gets its own address space in four parts: text (the machine code, read-only), data (global and static variables), the heap (memory allocated at run time with malloc or new , growing upward) and the stack (one frame per active function call, growing downward).

The program is loaded: its code in text, the global count = 5 in data, and one stack frame for main(). The heap is empty, and the free space between heap and stack is where both will grow.

- The program is loaded: its code in text, the global count = 5 in data, and one stack frame for main(). The heap is empty, and the free space between heap and stack is where both will grow.
- main() calls malloc(16). The heap grows upward by one block, and the pointer p, a local variable on the stack, holds its address.
- main() calls f(3). The stack grows downward: f gets a new frame with its argument x = 3 and its own local q.
- f() calls malloc(16) too, and a second block sits above the first: the heap grows up while the stack grows down.
- f() calls g(x + count), so g's frame holds y = 3 + 5 = 8. Each call adds a frame; deep recursion keeps adding them until the stack overflows.
- g returns 16 and f returns: their frames are gone the moment they return. The heap blocks stay until free() — and q's block is now unreachable, a memory leak.

Besides memory, a process owns resources the kernel tracks for it: open files, network connections, a current directory, a user identity and signal handlers.

### The process control block

The kernel describes every process with a process control block (PCB) , also called a task control block. On Linux it is the task_struct . The PCB is what lets a process stop and later continue exactly where it was.

### Process states

A process moves through states as it runs. The standard five-state model:

- New : being created; the PCB is being set up.
- Ready : in memory, able to run, waiting only for a CPU.
- Running : its instructions are executing on a CPU. With one core, at most one process is running.
- Waiting (Blocked): cannot continue until something happens, such as an I/O completion, a lock or a child exiting.
- Terminated : finished; the kernel is cleaning up.

The five states and the only legal moves between them, each arrow labelled with what causes it. The steps that follow trace one process from creation to exit.

- The five states and the only legal moves between them, each arrow labelled with what causes it. The steps that follow trace one process from creation to exit.
- The OS finishes creating the process and admits it: it is in memory and only needs a CPU.
- The scheduler dispatches it: its registers are loaded and it runs.
- It asks to read a file. It cannot continue until the disk answers, so it waits and gives up the CPU.
- The disk's interrupt reports the read is complete. The process becomes ready — not running: it must queue for the CPU like everyone else.
- Dispatched again, it continues where it left off: its saved program counter was in its PCB.
- The timer fires at the end of its time slice and the scheduler preempts it, back to ready.
- Dispatched again, it runs to its end.
- It calls exit(). The kernel frees its memory and files; its PCB remains until the parent collects the exit status.

Two transitions do not exist: Waiting never goes straight to Running (it must queue in Ready first), and Ready never goes to Waiting (only a running process can ask for I/O).

Systems that swap processes out of memory add two suspended states, ready-suspended and blocked-suspended . Three schedulers manage the whole picture: the long-term scheduler decides which new jobs are admitted, the short-term (CPU) scheduler picks the next ready process many times a second, and the medium-term scheduler swaps processes out and back in to control memory pressure.

### Context switch

A context switch moves the CPU from one process (or thread) to another. Something enters the kernel (a timer interrupt, an I/O request, a blocking system call), and the kernel saves the running process's state into its PCB and loads the next one's:

P1 is running: its program counter, stack pointer, registers and page-table base are live in the CPU. P2 is ready, and its PCB holds the values it had when it last stopped.

- P1 is running: its program counter, stack pointer, registers and page-table base are live in the CPU. P2 is ready, and its PCB holds the values it had when it last stopped.
- The timer interrupt enters the kernel. It saves P1's CPU state into P1's PCB and marks P1 ready — exactly what it needs to resume P1 later.
- The scheduler picks the next process from the ready queue: P2. Nothing useful has run for either process since the interrupt; the switch is pure overhead.
- The kernel loads P2's page-table base (0x2000) into the CPU: from now on addresses mean P2's memory, and the TLB's cached translations for P1 are useless. A switch between two threads of one process skips this step.
- Finally it restores P2's registers and returns to user mode: P2 continues at 0x52c4, exactly where it stopped, unaware it was ever off the CPU.

A context switch is pure overhead : the CPU does no useful work for either process during it. The direct cost is small, typically microseconds, but the indirect cost is larger: the new process finds the caches and the TLB filled with the old process's data. Switching between two threads of the same process skips the address-space switch, which is one reason threads are cheaper.

### Creating processes: fork() and exec()

On Unix-like systems, fork() creates a new process by duplicating the caller. The new child gets a copy of the parent's address space, open files and registers. fork() returns 0 in the child , the child's PID in the parent , and -1 in the parent if it failed. exec() then replaces the child's program with a new one, and wait() lets the parent collect the child's exit status.

```
#
include
<stdio.h>
#
include
<sys/wait.h>
#
include
<unistd.h>
int
main
(
void
)
{
pid_t
pid
=
fork
(
)
;
if
(
pid
<
0
)
{
perror
(
"fork"
)
;
/* no child was created */
return
1
;
}
if
(
pid
==
0
)
{
/* child */
printf
(
"child %d, parent %d\n"
,
getpid
(
)
,
getppid
(
)
)
;
execlp
(
"ls"
,
"ls"
,
"-l"
,
(
char
*
)
NULL
)
;
perror
(
"execlp"
)
;
/* reached only if exec failed */
return
1
;
}
waitpid
(
pid
,
NULL
,
0
)
;
/* parent waits and reaps the child */
printf
(
"parent: child %d finished\n"
,
pid
)
;
return
0
;
}
```

Copying a whole address space would be wasteful when the child calls exec at once, so modern kernels use copy-on-write : parent and child share the same physical pages, marked read-only, and a page is copied only when one of them writes to it.

Counting is a favourite question. Each fork() doubles the number of processes running past it, so three fork() calls in a row give 2³ = 8 processes (7 new ones), and a printf after them prints 8 times.

One process, P0, is about to run fork(); fork(); fork(); and then a printf.

- One process, P0, is about to run fork(); fork(); fork(); and then a printf.
- Fork 1: P0 runs it and gets a child, P1, so there are 2.
- Fork 2: each of the 2 processes alive runs it and gets a child, doubling the count to 4.
- Fork 3: each of the 4 processes alive runs it and gets a child, doubling the count to 8. The printf after them runs 8 times: 2³ = 8 processes, 7 of them new.

Two special cases:

- A zombie is a child that has exited but whose parent has not yet called wait() . Its memory is freed, but its PCB entry stays so the parent can read the exit status.
- An orphan is a child whose parent exited first. On Linux it is re-parented to init (PID 1) or a designated subreaper, which reaps it when it exits.

### Threads

A thread is the unit the CPU actually schedules: a program counter, a set of registers and a stack. A process with several threads runs several paths through the same program at once.

Every thread of a process runs the same code against the same globals, heap and open files, so they share data without any IPC — and can corrupt it without synchronization. Each thread has its own program counter, registers and stack, which is all a thread switch must change.

Why use threads: responsiveness (a UI thread stays live while a worker computes), resource sharing (threads share memory without any IPC), economy (creating a thread is far cheaper than a process) and scalability (threads run in parallel on multiple cores). The price is that shared memory needs synchronization, covered in Process Synchronization .

### Multithreading models

User threads must eventually run on kernel threads. The mapping is the multithreading model :

Many-to-one runs all of a process's user threads on one kernel thread, one-to-one gives each user thread a kernel thread of its own, and many-to-many multiplexes many user threads onto fewer kernel threads, remapping them as threads block.

- Many-to-one : switching is cheap, but one blocking call stops every thread and there is no parallelism. Early Java "green threads" worked this way.
- One-to-one : true parallelism and independent blocking, at the cost of a kernel thread per user thread. Linux (NPTL pthreads) and Windows use this model.
- Many-to-many : cheap threads with parallelism, but the runtime is harder to build. Go's goroutines and Java's virtual threads are runtime-level versions of it.
- Two-level : many-to-many, but a chosen user thread can also be bound to its own kernel thread.

### Common mistakes

- Saying threads share the stack. Each thread has its own stack; they share the heap and globals.
- Answering that fork() returns the parent's PID to the child. The child gets 0; it calls getppid() for the parent.
- Drawing a Waiting → Running arrow. A woken process always goes to Ready first.
- Thinking a zombie still uses CPU or memory. Only its PCB entry and exit status remain.
- Assuming more threads always means faster. Past the number of cores, extra CPU-bound threads add switching and contention.
- Calling a mode switch (a system call) a context switch.

### Interview questions

What is the difference between a process and a program? A program is a passive set of instructions in a file. A process is an active instance of it with a program counter, registers, an address space and resources. The same program can run as many independent processes.

What is stored in a PCB, and when is it used? The PID, state, saved program counter and registers, scheduling data, memory-management data, accounting data and open files. The kernel writes the CPU state into it when the process leaves the CPU and reads it back when the process is dispatched again.

How many processes does fork(); fork(); fork(); create? Eight processes in total, the original plus seven new ones, because each call doubles the processes that execute past it: 2³ = 8.

How many processes does fork() && fork() || fork(); create? Five in total. The parent's first fork is non-zero, so it runs the second fork and the || is skipped. The first child sees 0, skips the second fork and runs the third. The second child sees 0 from its fork and runs the third one too. That makes the parent plus four children.

What is a zombie process and how do you avoid one? A child that has exited but has not been reaped by its parent, so its entry stays in the process table. The parent avoids it by calling wait() or waitpid() , or by handling SIGCHLD ; if the parent exits, init adopts and reaps the child.

Why is a thread switch cheaper than a process switch? Threads of one process share the address space, so the kernel does not change the page table base and the TLB and caches stay useful. Only the registers, program counter and stack pointer change.

Which multithreading model does Linux use? One-to-one: every pthread is a kernel-scheduled task created with the clone() system call, sharing the address space with the other threads of its process.

When would you use processes instead of threads? When isolation matters more than sharing: a crash in one process does not take down the others, and their memory cannot be corrupted by each other. Modern browsers run web pages in separate processes for this reason.

Next, read CPU Scheduling Algorithms , or test yourself with the Operating Systems (Basic) skill test .

### What is the difference between a program and a process?

A program is a passive file of instructions on disk. A process is that program loaded into memory and running, with a program counter, registers, a stack, a heap and resources such as open files. One program can run as many processes at once, for example several browser or terminal windows.

### What is a PCB in an operating system?

The process control block is the kernel's record of one process. It holds the process ID, state, saved program counter and registers, scheduling information, memory-management information, accounting data and the list of open files. On a context switch the kernel saves the running process's CPU state into its PCB and loads the next one's.

### What are the states of a process?

The five-state model has New, Ready, Running, Waiting (also called Blocked) and Terminated. A process is admitted to Ready, dispatched to Running, preempted back to Ready, moved to Waiting when it needs I/O or an event, returned to Ready when that completes, and moved to Terminated when it exits.

### What is a context switch?

A context switch is the kernel saving the CPU state of the running process or thread into its control block and loading the saved state of another, so the CPU continues the second one where it left off. It is pure overhead, because no useful work is done during the switch, and it also leaves caches and the TLB cold.

### What does fork() return?

fork() creates a child process that is a copy of the caller. It returns twice: 0 in the child, and the child's process ID in the parent. If no child could be created it returns -1 in the parent only. Both processes continue from the instruction after the call.

### Why are threads called lightweight processes?

Because creating, switching and destroying a thread costs much less than doing the same for a process. Threads share their process's address space and resources, so the kernel does not set up a new page table or copy any memory, and switching between threads of one process keeps the same address space.


---

## Module 3: CPU Scheduling Algorithms

*Original URL: https://codekairo.com/notes/operating-systems/cpu-scheduling*

### Overview

Quick answer

### What is CPU scheduling in an operating system?

CPU scheduling is how the operating system decides which ready process runs on the CPU next and for how long. The short-term scheduler picks a process from the ready queue using a policy such as FCFS, SJF, SRTF, priority or Round Robin, aiming to keep the CPU busy while keeping waiting, turnaround and response times low and treating processes fairly.

- Scheduling criteria
- The example used throughout
- First-Come, First-Served (FCFS)
- Shortest Job First (SJF)
- Shortest Remaining Time First (SRTF)
- Priority scheduling
- Round Robin (RR)
- Multilevel queue and multilevel feedback queue
- Comparing the algorithms
- Simulating FCFS and Round Robin
- Common mistakes
- Interview questions
- Common questions
- Test yourself

The CPU scheduler decides which process in the ready queue runs next. A process alternates between CPU bursts (computing) and I/O bursts (waiting for a disk, the network or the user); whenever the running process blocks or is interrupted, the scheduler has to choose again. The choice decides how long everyone waits, so it is the most-asked computation topic in operating systems. This note defines the measures, then runs one example through every standard algorithm.

### Scheduling criteria

Scheduling decisions happen when a process (1) switches from running to waiting, (2) is interrupted from running back to ready, (3) moves from waiting to ready, or (4) terminates. A non-preemptive scheduler only decides in cases 1 and 4: once a process has the CPU it keeps it until it blocks or ends. A preemptive scheduler can also take the CPU away in cases 2 and 3.

The dispatcher carries the decision out: it performs the context switch, switches to user mode and jumps into the chosen process. The time it takes is the dispatch latency .

### The example used throughout

Four processes, times in milliseconds. For priority scheduling a smaller number means higher priority (a convention; always check which one a question uses).

The total burst is 16, and the CPU is never idle, so every schedule below ends at time 16. Ties are broken by earlier arrival.

### First-Come, First-Served (FCFS)

The ready queue is a FIFO queue: whoever arrived first runs first, to completion. It is non-preemptive, simple and fair in the sense of order, but one long process makes everyone behind it wait.

The bar is the CPU; each lane is one process, tinted while it sits in the ready queue. P3 needs 1 ms but waits 7 behind P1 and P2 — the convoy effect. Average waiting time 19/4 = 4.75 ms.

P3 needs one millisecond but waits seven: the convoy effect , where short processes queue behind a long one, and the I/O devices sit idle because the I/O-bound processes cannot run to issue their next request.

### Shortest Job First (SJF)

When the CPU is free, run the ready process with the shortest next CPU burst . Non-preemptive SJF is provably optimal for average waiting time when all processes are available at once, because moving a short job ahead of a long one reduces the short job's wait more than it increases the long one's.

Only P1 has arrived at 0, so it runs to 7. Then P2 (4), P3 (1), P4 (4) are ready and run shortest first: P3, P2, P4, the tie at 4 going to the earlier arrival. Average waiting 16/4 = 4 ms, down from 4.75 under FCFS.

The catch is that the OS does not know the next burst. It predicts it with an exponential average of past bursts: τ(n+1) = α·t(n) + (1 − α)·τ(n), where t(n) is the burst just measured and τ(n) the previous guess. With α = 0.5, an initial guess of 10 and measured bursts of 6 and then 4, the predictions are 0.5·6 + 0.5·10 = 8 and then 0.5·4 + 0.5·8 = 6. SJF can also starve a long job if short ones keep arriving.

### Shortest Remaining Time First (SRTF)

SRTF is preemptive SJF: whenever a process arrives, compare its burst with the remaining time of the running process and switch if the newcomer is shorter.

Only P1 has arrived, so it runs until P2 arrives at 2 and the times are compared again.

- Only P1 has arrived, so it runs until P2 arrives at 2 and the times are compared again.
- At 2, P2 arrives. P2 has the least time left, 4 (others: P1 5), so it preempts P1 and runs until P3 arrives at 4 and the times are compared again.
- At 4, P3 arrives. P3 has the least time left, 1 (others: P1 5, P2 2), so it preempts P2 and runs until it finishes at 5.
- At 5, P4 arrives. P2 has the least time left, 2 (others: P1 5, P4 4), so it runs until it finishes at 7.
- At 7, P4 has the least time left, 4 (others: P1 5), so it runs until it finishes at 11.
- At 11 only P1 is left, so it runs until it finishes at 16. Average waiting 12/4 = 3 ms, the lowest of any algorithm on this example.

SRTF gives the lowest average waiting time of any algorithm here, which is what theory predicts, but it makes the most context switches and has the same starvation risk as SJF.

### Priority scheduling

Each process has a priority and the CPU goes to the highest-priority ready process. SJF is the special case where priority is the predicted burst.

Non-preemptive: P1 is alone at 0 and keeps the CPU to 7; then the ready processes go by priority, P2 (1), P4 (2), P3 (4). Average waiting 22/4 = 5.5 ms.

- Non-preemptive: P1 is alone at 0 and keeps the CPU to 7; then the ready processes go by priority, P2 (1), P4 (2), P3 (4). Average waiting 22/4 = 5.5 ms.
- Preemptive: P2 (priority 1) takes the CPU from P1 the moment it arrives at 2. Average waiting 20/4 = 5 ms. In both, P3, the lowest priority, waits 11 — with more high-priority work arriving it could wait for ever, which aging prevents.

P3, the lowest priority, waits 11 ms in both versions, and under a steady stream of higher-priority work it could wait forever: that is starvation (indefinite blocking). The fix is aging : raise a process's priority the longer it waits, so it is eventually served.

### Round Robin (RR)

Round Robin is FCFS with preemption by a timer. Each process runs for at most one time quantum q, then goes to the back of the ready queue. It is the basis of time-sharing, because no process waits more than (n − 1)·q before its next turn when n processes are ready.

With q = 2, and the usual convention that a process arriving at the instant a quantum expires joins the queue before the preempted process:

Each process runs at most 2 ms, then rejoins the queue. 0–2: P1 runs one quantum of 2 and goes to the back of the queue, behind P2, which arrived at 2 as the quantum expired.

- Each process runs at most 2 ms, then rejoins the queue. 0–2: P1 runs one quantum of 2 and goes to the back of the queue, behind P2, which arrived at 2 as the quantum expired.
- 2–4: P2 runs one quantum of 2 and goes to the back of the queue, behind P3, which arrived at 4 as the quantum expired.
- 4–6: P1 runs one quantum of 2 and goes to the back of the queue, behind P4, which arrived at 5 during the slice.
- 6–7: P3 runs its last 1 ms and finishes, so it leaves the queue for good.
- 7–9: P2 runs its last quantum and finishes, so it leaves the queue for good.
- 9–11: P4 runs one quantum of 2 and goes to the back of the queue.
- 11–13: P1 runs one quantum of 2 and goes to the back of the queue.
- 13–15: P4 runs its last quantum and finishes, so it leaves the queue for good.
- 15–16: P1 runs its last 1 ms and finishes, so it leaves the queue for good. Average waiting 20/4 = 5 ms; no process ever waited more than 6 ms for its next turn.

Choosing the quantum. If q is larger than every burst, RR becomes FCFS. If q is tiny, most CPU time goes into context switches. A common textbook rule of thumb is that most CPU bursts (around 80%) should be shorter than q, while q stays much longer than a context switch. Average waiting time does not change smoothly with q either:

The same four processes under Round Robin with q from 1 to 8. The average does not move smoothly — 5 at q = 2, 7 at q = 3, 4.5 at q = 4 — and from q = 7, the longest burst, every process finishes in one turn and Round Robin is exactly FCFS.

### Multilevel queue and multilevel feedback queue

A multilevel queue splits the ready queue into several queues by process type, for example system, interactive and batch, each with its own algorithm (RR for interactive, FCFS for batch). Queues are served in fixed priority order, or each gets a share of CPU time. A process stays in its queue for life.

A multilevel feedback queue (MLFQ) lets processes move between queues based on behaviour. A typical setup:

- Queue 0: RR with q = 8. Every new process starts here.
- Queue 1: RR with q = 16. A process that used its whole quantum in queue 0 drops here.
- Queue 2: FCFS, for processes that used their whole quantum in queue 1 too.

A lower queue runs only when all higher queues are empty. Short, interactive processes finish or block within a quantum and stay high; long CPU-bound ones sink. Aging moves a process that has waited too long back up. An MLFQ is defined by the number of queues, each queue's algorithm, and the rules for moving up and down.

Real kernels are not one textbook algorithm. Linux's CFS scheduler, succeeded by EEVDF in kernel 6.6, shares CPU time between tasks in proportion to their weights instead of using fixed queues, while Windows uses preemptive scheduling over 32 priority levels.

### Comparing the algorithms

The same four processes under each algorithm:

Round Robin loses on waiting time to SJF and SRTF but nearly matches SRTF on response time, without needing to know any burst length.

### Simulating FCFS and Round Robin

This program replays the FCFS and Round Robin schedules above and prints the averages, using the same queueing rule for arrivals at a quantum boundary.

```
#
include
<algorithm>
#
include
<cstdio>
#
include
<deque>
#
include
<string>
#
include
<vector>
using
namespace
std
;
const
vector
<
string
>
NAMES
=
{
"P1"
,
"P2"
,
"P3"
,
"P4"
}
;
const
vector
<
int
>
ARRIVAL
=
{
0
,
2
,
4
,
5
}
;
// sorted by arrival
const
vector
<
int
>
BURST
=
{
7
,
4
,
1
,
4
}
;
const
int
N
=
4
;
void
report
(
const
string
&
name
,
const
vector
<
string
>
&
gantt
,
const
vector
<
int
>
&
finish
)
{
double
waiting
=
0
,
turnaround
=
0
;
for
(
int
i
=
0
;
i
<
N
;
i
++
)
{
int
tat
=
finish
[
i
]
-
ARRIVAL
[
i
]
;
turnaround
+=
tat
;
waiting
+=
tat
-
BURST
[
i
]
;
}
string line
;
for
(
size_t k
=
0
;
k
<
gantt
.
size
(
)
;
k
++
)
line
+=
(
k
?
" | "
:
""
)
+
gantt
[
k
]
;
printf
(
"%s: %s\n"
,
name
.
c_str
(
)
,
line
.
c_str
(
)
)
;
printf
(
"%s average waiting %.2f, turnaround %.2f\n"
,
name
.
c_str
(
)
,
waiting
/
N
,
turnaround
/
N
)
;
}
string
slice
(
int
i
,
int
from
,
int
to
)
{
return
NAMES
[
i
]
+
" "
+
to_string
(
from
)
+
"-"
+
to_string
(
to
)
;
}
void
fcfs
(
)
{
vector
<
string
>
gantt
;
vector
<
int
>
finish
(
N
)
;
int
time
=
0
;
for
(
int
i
=
0
;
i
<
N
;
i
++
)
{
time
=
max
(
time
,
ARRIVAL
[
i
]
)
;
gantt
.
push_back
(
slice
(
i
,
time
,
time
+
BURST
[
i
]
)
)
;
time
+=
BURST
[
i
]
;
finish
[
i
]
=
time
;
}
report
(
"FCFS"
,
gantt
,
finish
)
;
}
void
roundRobin
(
int
quantum
)
{
vector
<
string
>
gantt
;
vector
<
int
>
left
=
BURST
,
finish
(
N
)
;
deque
<
int
>
ready
;
int
next
=
0
,
time
=
0
;
while
(
next
<
N
||
!
ready
.
empty
(
)
)
{
if
(
ready
.
empty
(
)
)
time
=
max
(
time
,
ARRIVAL
[
next
]
)
;
while
(
next
<
N
&&
ARRIVAL
[
next
]
<=
time
)
ready
.
push_back
(
next
++
)
;
int
i
=
ready
.
front
(
)
;
ready
.
pop_front
(
)
;
int
run
=
min
(
quantum
,
left
[
i
]
)
;
gantt
.
push_back
(
slice
(
i
,
time
,
time
+
run
)
)
;
time
+=
run
;
left
[
i
]
-=
run
;
// arrivals during the slice queue ahead of the preempted process
while
(
next
<
N
&&
ARRIVAL
[
next
]
<=
time
)
ready
.
push_back
(
next
++
)
;
if
(
left
[
i
]
>
0
)
ready
.
push_back
(
i
)
;
else
finish
[
i
]
=
time
;
}
report
(
"RR q="
+
to_string
(
quantum
)
,
gantt
,
finish
)
;
}
int
main
(
)
{
fcfs
(
)
;
roundRobin
(
2
)
;
return
0
;
}
```

Output

```
FCFS: P1 0-7 | P2 7-11 | P3 11-12 | P4 12-16
FCFS average waiting 4.75, turnaround 8.75
RR q=2: P1 0-2 | P2 2-4 | P1 4-6 | P3 6-7 | P2 7-9 | P4 9-11 | P1 11-13 | P4 13-15 | P1 15-16
RR q=2 average waiting 5.00, turnaround 9.00
```

### Common mistakes

- Computing waiting time as start time − arrival time under a preemptive algorithm. That is response time; waiting time is turnaround − burst and counts every stretch in the ready queue.
- Comparing a newcomer under SRTF with the running process's original burst instead of its remaining time.
- Forgetting idle gaps: if no process has arrived yet, the CPU idles and the timeline jumps to the next arrival.
- Reading a larger priority number as higher priority without checking the question's convention.
- In Round Robin, putting the preempted process ahead of a process that arrived at the same instant; most textbooks queue the newcomer first, and the answer changes if you do not.
- Saying Round Robin cannot starve because it is fair, then claiming the same for SJF. SJF and priority scheduling can starve; FCFS and RR cannot.

### Interview questions

Why is SJF optimal, and why is it not used directly? Running the shortest job first minimizes the total time everyone else spends waiting behind it, which gives the minimum average waiting time for a fixed set of jobs. It is impractical because the next CPU burst is unknown, so it must be predicted, and long jobs can starve.

What is the difference between SJF and SRTF? SJF is non-preemptive: a chosen process runs its whole burst. SRTF is its preemptive version: a newly arrived process with a shorter burst than the running process's remaining time takes the CPU.

How does the time quantum affect Round Robin? A very large quantum turns RR into FCFS and hurts response time. A very small quantum gives quick responses but wastes CPU time on context switches. The quantum should be large compared with the context-switch time and longer than most CPU bursts.

What is starvation, and how does aging solve it? Starvation is a ready process waiting indefinitely because others are always preferred, as with a low-priority process in priority scheduling. Aging raises a process's priority the longer it waits, so it eventually reaches the top and runs.

What is the difference between a multilevel queue and a multilevel feedback queue? In a multilevel queue a process is assigned to one queue permanently. In a multilevel feedback queue it moves: using a whole quantum pushes it down, and waiting too long (aging) can move it up, so the scheduler learns which processes are interactive.

Which algorithms are preemptive? SRTF, Round Robin and preemptive priority scheduling. FCFS and SJF are non-preemptive, and multilevel queues are usually preemptive between queues.

What is the difference between turnaround time and response time? Turnaround time runs from arrival to completion and matters for batch jobs. Response time runs from arrival to the first moment on the CPU and matters for interactive programs, where the user wants to see something start.

Next, read Process Synchronization , or practise these computations in the Operating Systems (Intermediate) skill test .

### What is the difference between preemptive and non-preemptive scheduling?

In non-preemptive scheduling a process keeps the CPU until it finishes or blocks for I/O. In preemptive scheduling the OS can take the CPU away, for example when a time slice ends or a higher-priority process arrives. FCFS and SJF are non-preemptive; SRTF and Round Robin are preemptive; priority scheduling can be either.

### How do you calculate turnaround time and waiting time?

Turnaround time is completion time minus arrival time. Waiting time is turnaround time minus burst time, which is the total time the process spent in the ready queue. Response time is the time of first execution minus arrival time. Averages are the sums divided by the number of processes.

### Which CPU scheduling algorithm is the best?

None is best for every goal. SJF gives the minimum average waiting time for a set of processes that arrive together, and SRTF does the same when they arrive over time, but both need burst times nobody knows in advance and can starve long jobs. Round Robin gives the best response time for interactive work. Real systems combine ideas in multilevel feedback queues.

### What is the convoy effect?

The convoy effect happens in FCFS when one long CPU-bound process holds the CPU while many short processes wait behind it, like cars stuck behind a slow truck. Average waiting time rises sharply and I/O devices sit idle, because the short I/O-bound processes cannot run to issue their next request.

### What is aging in CPU scheduling?

Aging is gradually raising the priority of a process the longer it waits in the ready queue. It prevents starvation in priority scheduling: however low a process's priority starts, it eventually becomes high enough to run. A scheduler might, for example, raise a waiting process's priority by one level every few hundred milliseconds.

### What happens if the time quantum in Round Robin is too large or too small?

If the quantum is larger than every burst, Round Robin behaves exactly like FCFS. If it is very small, the CPU spends a large share of its time on context switches instead of useful work. A common textbook rule of thumb is to choose a quantum longer than most CPU bursts, so that most processes finish a burst within one slice.


---

## Module 4: Process Synchronization

*Original URL: https://codekairo.com/notes/operating-systems/process-synchronization*

### Overview

Quick answer

### What is process synchronization in an operating system?

Process synchronization is coordinating processes or threads that share data so that the result does not depend on the order in which they happen to run. Its core is the critical section problem: allow only one process at a time into code that touches shared data, while guaranteeing progress and bounded waiting. Tools include Peterson's algorithm, atomic hardware instructions, mutex locks, semaphores and monitors.

- Race conditions
- The critical section problem
- Peterson's solution
- Hardware support
- Mutex locks
- Semaphores
- Monitors
- Busy waiting vs blocking
- Mutex vs semaphore
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Processes and threads that share data are cooperating : a producer fills a buffer a consumer empties, two threads update one bank balance. Because the scheduler can interrupt either of them between any two machine instructions, their steps can interleave in ways the programmer never intended. Process synchronization is the set of rules and tools that make shared data come out right whatever the interleaving. Every tool below solves the same problem, the critical section problem, at a different level.

### Race conditions

counter++ looks like one step, but the CPU runs it as three: load the value into a register, add one, store it back. Suppose counter is 5, thread T1 runs counter++ and thread T2 runs counter-- at the same time:

Each one-line statement is three instructions: load counter into a register, change the register, store it back. counter starts at 5, and the two threads run interleaved in the order on the bottom row.

- Each one-line statement is three instructions: load counter into a register, change the register, store it back. counter starts at 5, and the two threads run interleaved in the order on the bottom row.
- Step 1: T1 loads counter (5) into r1.
- Step 2: T1 changes only its own register: r1 = 6. counter in memory is still 5.
- Step 3: T2 loads counter (5) into r2. T1 has not stored yet, so T2 reads the old value — this is where the update gets lost.
- Step 4: T2 changes only its own register: r2 = 4. counter in memory is still 5.
- Step 5: T1 stores r1: counter = 6.
- Step 6: T2 stores r2: counter = 4, overwriting the 6 that T1 stored a moment ago.
- One increment and one decrement should leave 5, but this run ends at 4. Of all 20 interleavings of the six instructions, 2 give 5, 9 give 4 and 9 give 6: the answer depends on timing.

The right answer is 5, but this interleaving gives 4, and swapping the last two stores gives 6. A race condition is exactly this: the outcome depends on the timing of concurrent accesses to shared data where at least one is a write. Races are hard to find because they rarely show: only 2 of the 20 possible interleavings here are right, but a thread is so seldom preempted inside those three instructions that almost every run takes one of those two.

### The critical section problem

A critical section is the part of a program that accesses shared data. Each process loops through four parts: an entry section that asks permission, the critical section, an exit section that announces it has left, and the remainder section , everything else.

Each process loops through four sections. Only the critical section touches the shared data. P0 is inside it, so P1's entry section holds P1 back until P0's exit section announces it has left.

A correct solution to the critical section problem must satisfy three requirements:

- Mutual exclusion. If one process is in its critical section, no other process is in its own.
- Progress. If no process is in its critical section and some want to enter, only processes that are not in their remainder section take part in choosing the next one, and the choice cannot be postponed forever.
- Bounded waiting. Once a process has asked to enter, there is a limit on how many times others may enter before it does. This rules out starvation.

No assumption may be made about the relative speed of the processes, only that each makes progress when it runs.

A tempting broken attempt uses one shared turn variable: process i enters only when turn == i and sets turn to the other on exit. It gives mutual exclusion but violates progress : the processes must strictly alternate, so if P0 wants to enter twice while P1 is busy elsewhere, P0 waits for nothing.

### Peterson's solution

Peterson's algorithm solves the problem for two processes in software, with two shared variables: flag[i] says process i wants to enter, and turn says whose turn it is to give way.

```
int
flag
[
2
]
=
{
0
,
0
}
;
/* flag[i] == 1: process i wants to enter */
int
turn
;
/* who must give way if both want to enter */
void
enter
(
int
i
)
{
/* i is 0 or 1 */
int
j
=
1
-
i
;
flag
[
i
]
=
1
;
/* I want to enter */
turn
=
j
;
/* but you go first if you want to as well */
while
(
flag
[
j
]
&&
turn
==
j
)
;
/* busy wait */
}
void
leave
(
int
i
)
{
flag
[
i
]
=
0
;
/* I am out */
}
```

Here it is run with both processes competing:

P0 sets flag[0] = 1: it wants to enter.

- P0 sets flag[0] = 1: it wants to enter.
- P1 sets flag[1] = 1: it wants to enter.
- P0 sets turn = 1, offering to let P1 go first.
- P1 sets turn = 0, offering to let P0 go first. Both want in, and turn holds whichever value was written last — so exactly one of them will wait.
- P0 tests: turn is 0, not 1, so it leaves the loop and enters its critical section.
- P1 tests: flag[0] is 1 and turn is 0, so it spins in the while loop.
- P0 leaves its critical section and sets flag[0] = 0.
- P1 tests: flag[0] is 0, so it leaves the loop and enters its critical section. Each entered once and they were never inside together: whoever wrote turn last waited.

Why it satisfies all three requirements:

- Mutual exclusion. Pi passes its loop only if flag[j] is 0 or turn == i . If both were inside, both flags would be 1, so turn would have to equal both 0 and 1 at once.
- Progress. If Pj does not want to enter, flag[j] is 0 and Pi enters at once. If both want to, turn holds one value, so exactly one of them gets in.
- Bounded waiting. When Pj leaves and tries to enter again, it sets turn = i itself, so Pi waits for at most one entry by Pj.

Peterson's solution is the textbook proof that the problem can be solved in software, but it is not guaranteed to work on modern processors as written. CPUs and compilers may reorder independent loads and stores, so Pi could read flag[j] before its own write to flag[i] is visible. Real code needs memory barriers or the atomic instructions below.

### Hardware support

Disabling interrupts around the critical section works on a single CPU, because nothing can preempt the running process. It fails on a multiprocessor, where another core keeps running, and it is far too dangerous to let user programs do.

Modern CPUs instead provide instructions that read and modify a memory word atomically , as one indivisible step.

Test-and-set sets a word to true and returns its old value:

```
/* the hardware executes this as one atomic step */
bool
test_and_set
(
bool
*
target
)
{
bool old
=
*
target
;
*
target
=
true
;
return
old
;
}
bool lock
=
false
;
void
acquire
(
void
)
{
while
(
test_and_set
(
&
lock
)
)
;
}
/* spin until it was false */
void
release
(
void
)
{
lock
=
false
;
}
```

Compare-and-swap (CAS) writes a new value only if the word still holds the expected one, and returns what it held:

```
/* the hardware executes this as one atomic step */
int
compare_and_swap
(
int
*
value
,
int
expected
,
int
new_value
)
{
int
old
=
*
value
;
if
(
old
==
expected
)
*
value
=
new_value
;
return
old
;
}
int
lock
=
0
;
void
acquire
(
void
)
{
while
(
compare_and_swap
(
&
lock
,
0
,
1
)
!=
0
)
;
}
void
release
(
void
)
{
lock
=
0
;
}
```

Both locks give mutual exclusion and progress but not bounded waiting: an unlucky process can keep losing the race. A version with a waiting[] array, where the leaving process hands the lock to the next waiter in cyclic order, adds bounded waiting. CAS is also the basis of atomic variables ( std::atomic , Java's AtomicInteger ) and lock-free data structures.

### Mutex locks

A mutex (mutual exclusion lock) wraps all this in two calls: acquire() before the critical section and release() after it. Only the thread that acquired a mutex may release it.

A mutex that waits by looping is a spinlock . One that waits by putting the thread to sleep until the lock is released is a blocking (sleeping) mutex. Spinning wastes CPU but avoids two context switches, so kernels use spinlocks for critical sections only a few instructions long on multiprocessors, and sleeping locks for anything that might take longer.

### Semaphores

A semaphore S, introduced by Dijkstra, is an integer accessed only through two atomic operations: wait (P, from the Dutch proberen , to test) and signal (V, verhogen , to increment). The simplest definition busy-waits:

```
wait(S):   while (S <= 0) ;  // busy wait
           S--
signal(S): S++
```

Real implementations block instead, keeping a queue of waiting processes. The value may then go negative, and its magnitude is the number of processes waiting:

```
wait(S):   S.value--
           if (S.value < 0) { add this process to S.queue; block() }
signal(S): S.value++
           if (S.value <= 0) { remove a process P from S.queue; wakeup(P) }
```

There are two kinds:

- A binary semaphore takes only 0 and 1 and is used like a lock: initialize it to 1, wait before the critical section and signal after it.
- A counting semaphore is initialized to the number of identical resources.

Worked trace: a counting semaphore for two printers starts at 2, and processes A, B, C and D each call wait , then A and B finish and call signal . The value ends at 0, with C and D printing and nobody waiting.

Two printers, so the semaphore starts at 2. Four processes will each call wait() before printing and signal() when they finish.

- Two printers, so the semaphore starts at 2. Four processes will each call wait() before printing and signal() when they finish.
- A calls wait(): the value drops to 1, not below zero, so A goes ahead and takes a printer.
- B calls wait(): the value drops to 0, not below zero, so B goes ahead and takes a printer.
- C calls wait(): the value drops to −1, below zero, so C joins the queue and blocks. −1 means one process is waiting.
- D calls wait(): the value drops to −2, below zero, so D joins the queue and blocks. −2 means two processes are waiting.
- A calls signal(): the value rises to −1, still not positive, so the first waiter, C, wakes and takes the printer A freed.
- B calls signal(): the value rises to 0, still not positive, so the first waiter, D, wakes and takes the printer B freed. The value is back to 0: both printers busy, nobody waiting.

Semaphores also impose ordering . To make statement S2 in P2 run only after S1 in P1, share a semaphore synch initialized to 0: P1 runs S1 then signal(synch) ; P2 runs wait(synch) then S2.

Semaphores are powerful but easy to misuse. Swapping wait and signal breaks mutual exclusion, writing wait twice deadlocks, and forgetting one breaks everything. Two processes doing wait(S); wait(Q) and wait(Q); wait(S) can deadlock , each holding one semaphore and waiting for the other.

### Monitors

A monitor is a language construct that groups shared data with the procedures that operate on it, and guarantees that only one process is active inside the monitor at a time . The compiler inserts the locking, so the programmer cannot forget it.

For waiting on a condition, a monitor has condition variables . x.wait() suspends the caller and releases the monitor; x.signal() resumes one process waiting on x, and does nothing if none is waiting . That is the key difference from a semaphore's signal , which is remembered in the count.

```
monitor Account {
    int balance = 0
    condition funds

    procedure deposit(amount) {
        balance = balance + amount
        funds.signal()
    }
    procedure withdraw(amount) {
        while (balance < amount)
            funds.wait()         // releases the monitor while waiting
        balance = balance - amount
    }
}
```

After signal , either the signaller waits and the woken process runs at once (Hoare semantics, signal-and-wait ) or the signaller continues and the woken process runs later (Mesa semantics, signal-and-continue ). Most real systems, including Java and pthreads, use Mesa semantics, which is why the condition is rechecked in a while loop rather than an if . In Java, every object is a monitor: synchronized methods give the mutual exclusion, and wait() , notify() and notifyAll() act as one condition variable.

### Mutex vs semaphore

A related trap is priority inversion : a low-priority process holds a lock a high-priority process needs, and a medium-priority process preempts the low one, so the high-priority process waits on the medium one. The fix is priority inheritance : the lock holder temporarily runs at the priority of the highest process waiting for it.

L takes the lock at 1. H arrives at 2, needs the lock and blocks. M arrives at 3 and, outranking L, runs for 4 units while L still holds the lock — so H, the most urgent task, waits on M and finishes only at 10.

- L takes the lock at 1. H arrives at 2, needs the lock and blocks. M arrives at 3 and, outranking L, runs for 4 units while L still holds the lock — so H, the most urgent task, waits on M and finishes only at 10.
- With priority inheritance, L runs at H's priority while H waits for its lock, so M cannot preempt it. L finishes its critical section at 4, H takes the lock and finishes at 6, and M runs after.

A priority inversion famously reset the Mars Pathfinder lander's computer in 1997 until engineers enabled priority inheritance remotely.

### Common mistakes

- Thinking count++ is atomic because it is one line of code. It is a load, an add and a store.
- Listing the three requirements as "mutual exclusion, no deadlock, no starvation". The standard names are mutual exclusion, progress and bounded waiting.
- Saying a condition variable's signal works like a semaphore's. A condition signal with no waiter is lost; a semaphore signal is counted.
- Using if instead of while around a condition wait under Mesa semantics, so a woken thread acts on a condition that is no longer true.
- Claiming Peterson's algorithm works unchanged on modern multicore CPUs. Without memory barriers, reordering can break it.
- Treating a binary semaphore and a mutex as identical. The mutex has an owner; the semaphore does not.

### Interview questions

What is the critical section problem? Designing a protocol so that when processes share data, at most one is executing code that accesses it at any time. A solution must give mutual exclusion, progress and bounded waiting, without assuming anything about relative process speeds.

Explain Peterson's solution. Each of the two processes sets its own flag to say it wants to enter, then sets turn to the other process, and waits while the other wants to enter and it is the other's turn. Whoever wrote turn last waits, so exactly one enters, and each waits for at most one entry by the other.

What does wait() do on a semaphore whose value is 0? In the blocking implementation the value becomes −1, the caller is added to the semaphore's queue and blocked. It stays blocked until another process calls signal() , which increments the value and wakes one waiting process.

Why can disabling interrupts not be used for mutual exclusion on a multiprocessor? Disabling interrupts only stops preemption on the CPU that did it. Other cores continue to run and can enter the critical section, and disabling interrupts on every core is slow and unsafe.

What is a spinlock, and when is it preferred? A lock whose waiters loop testing it instead of sleeping. It is preferred when critical sections are very short and the system has several cores, because spinning briefly costs less than two context switches.

What is the difference between a monitor and a semaphore? A semaphore is a low-level counter the programmer must call correctly everywhere. A monitor is a language construct where mutual exclusion is automatic, with condition variables for waiting, which makes misuse much harder.

What is priority inversion and how is it solved? A high-priority process waits for a lock held by a low-priority process, which in turn is preempted by medium-priority work, so the high-priority process is effectively delayed by lower ones. Priority inheritance raises the lock holder to the waiter's priority until it releases the lock.

Next, read Classic Synchronization Problems , or test yourself with the Operating Systems (Intermediate) skill test .

### What is a race condition?

A race condition is when several processes or threads access shared data concurrently, at least one of them writes, and the final result depends on the exact interleaving of their instructions. The classic example is two threads incrementing one counter: both read the old value, both add one, and one update is lost.

### What are the three requirements of a critical section solution?

Mutual exclusion: at most one process is inside its critical section at a time. Progress: if none is inside and some want to enter, one of them is chosen without indefinite delay, and processes outside the protocol cannot block the choice. Bounded waiting: after a process asks to enter, other processes can enter only a limited number of times before it does.

### What is the difference between a mutex and a semaphore?

A mutex is a lock with an owner: the thread that locks it must unlock it, and it lets exactly one thread in. A semaphore is a counter with wait and signal operations and no owner, so one thread can signal what another waits on. A counting semaphore admits up to n threads, which makes it suitable for counting resources and for signalling.

### What is the difference between binary and counting semaphores?

A binary semaphore takes only the values 0 and 1 and is used like a lock for mutual exclusion. A counting semaphore can take any non-negative value and is initialized to the number of identical resources, such as three printers; each wait takes one resource and each signal returns one.

### What is busy waiting?

Busy waiting, or spinning, is a process repeatedly testing a condition in a loop until it becomes true, using the CPU the whole time. It wastes CPU cycles, but for very short waits on a multiprocessor it can be cheaper than blocking, because it avoids two context switches. A lock that busy-waits is called a spinlock.

### What is a monitor in OS?

A monitor is a high-level synchronization construct that bundles shared data with the procedures that use it and guarantees that only one process is active inside it at a time. Processes that must wait for a condition use condition variables with wait and signal. Java's synchronized methods with wait and notify follow the monitor model.


---

## Module 5: Classic Synchronization Problems

*Original URL: https://codekairo.com/notes/operating-systems/classic-synchronization-problems*

### Overview

Quick answer

### What are the classic problems of synchronization in operating systems?

The three classic synchronization problems are the bounded-buffer (producer-consumer) problem, the readers-writers problem and the dining philosophers problem. Each models a real pattern: passing items through a fixed-size buffer, letting many readers but only one writer at a time use shared data, and processes that each need several shared resources at once. They are used to test any new synchronization tool, usually semaphores or monitors.

- The producer-consumer (bounded-buffer) problem
- The readers-writers problem
- The dining philosophers problem
- The three problems side by side
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Every new synchronization tool is tested on the same few problems. They are not puzzles for their own sake: each is a small model of something operating systems and servers do all the time, and each has a classic trap. Interviewers ask you to write the semaphore solution and then explain what goes wrong if one line moves. The tools used here, semaphores and monitors, are explained in Process Synchronization .

### The producer-consumer (bounded-buffer) problem

A producer creates items and puts them into a buffer of n slots; a consumer takes them out. The producer must wait when the buffer is full, the consumer must wait when it is empty, and the two must never modify the buffer at the same time. Pipes between processes, print queues and work queues all have this shape.

The solution uses three semaphores:

```
producer:
while (true) {
    item = produce()
    wait(empty)        // wait for a free slot
    wait(mutex)
    insert(item)
    signal(mutex)
    signal(full)       // one more filled slot
}

consumer:
while (true) {
    wait(full)         // wait for a filled slot
    wait(mutex)
    item = remove()
    signal(mutex)
    signal(empty)      // one more free slot
    consume(item)
}
```

empty and full do the counting and make processes wait; mutex only protects the buffer's internal pointers. At any moment empty + full equals n, except while a process is between its two operations.

A short run with n = 2, where the producer makes three items before the consumer runs, using blocking semaphores (a negative value counts the waiters):

A two-slot buffer with nothing in it: empty = 2 free slots, full = 0 filled slots, mutex = 1. The producer will make A, B and C; the consumer will take one item.

- A two-slot buffer with nothing in it: empty = 2 free slots, full = 0 filled slots, mutex = 1. The producer will make A, B and C; the consumer will take one item.
- The producer waits on empty (now 1), takes the mutex, puts A in slot 0, releases the mutex and signals full (now 1).
- The producer waits on empty (now 0), takes the mutex, puts B in slot 1, releases the mutex and signals full (now 2).
- For C the producer calls wait(empty): the value goes to −1, so it blocks in empty's queue. It holds nothing else — it has not touched the mutex.
- The consumer waits on full (1 left), removes A from slot 0, and its signal(empty) raises empty to 0 — not above zero, so it wakes the producer, handing it the freed slot.
- The producer, already past wait(empty), takes the mutex, puts C in slot 0 — the buffer wraps round — and signals full. Now empty = 0, full = 2: the buffer is full again with B and C.

The trap: the order of the waits. If the producer called wait(mutex) before wait(empty) , a full buffer would leave it blocked while holding the mutex, and the consumer could never get in to free a slot: a deadlock .

The buffer is full: empty = 0, full = 2. This producer has its two waits the wrong way round — wait(mutex) first, then wait(empty).

- The buffer is full: empty = 0, full = 2. This producer has its two waits the wrong way round — wait(mutex) first, then wait(empty).
- The producer takes the mutex (now 0), then calls wait(empty).
- empty drops to −1: no free slot, so the producer blocks — while still holding the mutex.
- The consumer could free a slot: it passes wait(full), then calls wait(mutex) — held by the producer — and blocks too. Each waits for the other, for ever: a deadlock from swapping two lines.

Always wait on the counting semaphore first. The order of the two signal calls, by contrast, does not affect correctness.

### The readers-writers problem

Shared data, such as a database table or a configuration file, is read by many processes and occasionally updated. Any number of readers may read at once, because reading changes nothing, but a writer needs exclusive access: no other writer and no reader.

### First variant: readers have priority

No reader waits unless a writer already has the data.

```
semaphore rw_mutex = 1   // held by one writer, or by the readers as a group
semaphore mutex = 1      // protects read_count
int read_count = 0

writer:
    wait(rw_mutex)
    ... write ...
    signal(rw_mutex)

reader:
    wait(mutex)
    read_count++
    if (read_count == 1) wait(rw_mutex)    // first reader locks writers out
    signal(mutex)
    ... read ...
    wait(mutex)
    read_count--
    if (read_count == 0) signal(rw_mutex)  // last reader lets writers in
    signal(mutex)
```

Only the first reader competes with writers for rw_mutex ; later readers just increment the count and walk in. mutex exists because read_count++ is itself a race condition. If a writer is writing and several readers arrive, the first reader blocks on rw_mutex while holding mutex , and the others queue on mutex .

The cost is writer starvation : if readers keep arriving so that read_count never falls to 0, a writer waits forever.

### Second variant and the fair solution

The second variant gives writers priority: once a writer is waiting, no new reader may start. It needs extra counters and semaphores, and now readers can starve under a steady stream of writers.

A fair solution adds one semaphore, queue , initialized to 1, that every reader and writer must pass through first:

```
writer:                         reader:
    wait(queue)                     wait(queue)
    wait(rw_mutex)                  wait(mutex)
    signal(queue)                   read_count++
    ... write ...                   if (read_count == 1) wait(rw_mutex)
    signal(rw_mutex)                signal(mutex)
                                    signal(queue)
                                    ... read ...
                                    (leave as in the first variant)
```

A writer waiting in queue stops new readers from slipping past it, so processes are served roughly in arrival order (exactly, if the semaphore's queue is first-in, first-out). The same arrivals under both solutions:

Readers first: W arrives at 3, but R3 and R4 arrive while others are still reading, so read_count never falls to zero. W waits 9 units, until the last reader leaves at 12.

- Readers first: W arrives at 3, but R3 and R4 arrive while others are still reading, so read_count never falls to zero. W waits 9 units, until the last reader leaves at 12.
- Fair: everyone passes the queue semaphore first. W takes it at 3 and holds it until it gets rw_mutex at 6, so R3 and R4 queue behind W. W waits only 3.

Real systems offer this as a reader-writer lock , such as POSIX pthread_rwlock_t or Java's ReentrantReadWriteLock , whose fairness policy varies by implementation.

### The dining philosophers problem

Five philosophers sit at a round table with one bowl of rice each and five chopsticks, one between each pair of neighbours. A philosopher alternates between thinking and eating, and needs both neighbouring chopsticks to eat. It models processes that need several shared resources at once.

The obvious solution gives each chopstick a semaphore:

```
semaphore chopstick[5] = {1, 1, 1, 1, 1}

philosopher i:
while (true) {
    think()
    wait(chopstick[i])              // left
    wait(chopstick[(i + 1) % 5])    // right
    eat()
    signal(chopstick[(i + 1) % 5])
    signal(chopstick[i])
}
```

No two neighbours can eat at once, but it can deadlock : if all five pick up their left chopstick at the same moment, each waits for its right one, held by its neighbour. Every philosopher holds one resource and waits for another in a circle, which is exactly the circular wait described in Deadlocks in Operating Systems .

Five philosophers, five chopsticks c0–c4: philosopher i needs chopstick i on one side and chopstick (i + 1) mod 5 on the other. Here everyone gets hungry at the same moment.

- Five philosophers, five chopsticks c0–c4: philosopher i needs chopstick i on one side and chopstick (i + 1) mod 5 on the other. Here everyone gets hungry at the same moment.
- Each philosopher picks up the left chopstick, wait(chopstick[i]). All five succeed, and the table is now empty.
- Each now calls wait on the right chopstick, which the neighbour holds. P0 waits for P1, P1 for P2, and round to P4 waiting for P0: a circular wait, and nobody ever eats.
- The fix by ordering: everyone picks up the lower-numbered chopstick first. For P0–P3 that is still the left one, but P4 needs c0 and c4, so it reaches for c0 first — and finds P0 holding it.
- P4 waits holding nothing, so c4 stays free and P3 picks it up and eats. No cycle can close; when P3 puts its chopsticks down, the others eat in turn.

### Deadlock-free fixes

- At most four at the table. A counting semaphore seats initialized to 4 is taken before the first chopstick. With four philosophers and five chopsticks, at least one of them can get both.
- Order the resources. Each philosopher picks up the lower-numbered chopstick first. Philosophers 0 to 3 take their left first, but philosopher 4 needs chopsticks 4 and 0, so takes 0 first. No cycle of waiting can form. An equivalent rule: odd-numbered philosophers take left first, even-numbered take right first.
- Both or neither. A philosopher picks up chopsticks only when both are free, with the check and the pick-up done inside a critical section, as in the monitor below.

```
monitor DiningPhilosophers {
    enum { THINKING, HUNGRY, EATING } state[5]
    condition self[5]

    pickup(i):
        state[i] = HUNGRY
        test(i)
        if (state[i] != EATING) self[i].wait()

    putdown(i):
        state[i] = THINKING
        test((i + 4) % 5)        // the left neighbour may eat now
        test((i + 1) % 5)        // the right neighbour may eat now

    test(i):
        if (state[(i + 4) % 5] != EATING and state[i] == HUNGRY
            and state[(i + 1) % 5] != EATING) {
            state[i] = EATING
            self[i].signal()
        }
}
```

A philosopher eats only when neither neighbour is eating, so no one ever holds one chopstick while waiting for the other, and deadlock is impossible. Starvation is still possible : two neighbours who take turns eating can keep the philosopher between them hungry forever. Preventing that needs an extra rule, such as letting a philosopher who has waited too long go first.

### The three problems side by side

The sleeping barber problem, a barber who sleeps when there are no customers and a waiting room with n chairs, is a fourth classic sometimes asked; it is the bounded buffer again, with customers as producers and the barber as the consumer.

### Common mistakes

- Swapping wait(empty) and wait(mutex) in the producer, or wait(full) and wait(mutex) in the consumer, which can deadlock.
- Using only a mutex for the bounded buffer: it prevents corruption but cannot make the producer wait for space.
- Forgetting that read_count needs its own mutex: incrementing it is a race condition like any other.
- Saying the first readers-writers solution is starvation-free. Writers can starve.
- Claiming the monitor solution for dining philosophers prevents starvation. It prevents deadlock only.
- Mixing up which side does what: the producer waits on empty and signals full ; the consumer waits on full and signals empty .

### Interview questions

Why does the bounded buffer need three semaphores and not one? The mutex only gives exclusive access to the buffer. The producer must also wait while the buffer is full and the consumer while it is empty, which needs counters of free and filled slots. empty and full are those counters, and blocking on them is how waiting happens.

What happens if the consumer signals full instead of empty after removing an item? The count of filled slots goes up although one was emptied, so consumers will try to remove items that do not exist, and producers never learn a slot was freed. The buffer state and the semaphores drift apart and the program breaks.

In the first readers-writers solution, why do only the first and last readers touch rw_mutex ? Readers lock writers out as a group. The first reader to arrive acquires rw_mutex on behalf of all readers, and the last one to leave releases it; readers in between only update read_count .

How would you avoid starvation of writers? Give writers priority once one is waiting, so new readers are held back, or serve all processes in arrival order with an extra queue semaphore that both readers and writers must pass first.

Which deadlock condition does each dining-philosophers fix break? Ordering chopsticks breaks circular wait. Taking both or neither breaks hold-and-wait. Limiting the table to four keeps a cycle from closing, since one philosopher can always finish and release.

Is the dining philosophers problem only about deadlock? No. A solution must also avoid starvation, and the simple deadlock-free solutions do not guarantee that. It also asks for concurrency: two non-neighbouring philosophers should be able to eat at the same time.

Next, read Deadlocks in Operating Systems , or try the Operating Systems (Intermediate) skill test .

### How is the producer-consumer problem solved using semaphores?

Use three semaphores: mutex initialized to 1 to protect the buffer, empty initialized to the buffer size to count free slots, and full initialized to 0 to count filled slots. The producer waits on empty then mutex, inserts, and signals mutex then full. The consumer waits on full then mutex, removes, and signals mutex then empty.

### Why does the order of wait operations matter in the bounded buffer problem?

If the producer calls wait(mutex) before wait(empty) when the buffer is full, it blocks on empty while holding mutex. The consumer then blocks on mutex and can never remove an item to free a slot, so both wait forever. Always wait on the counting semaphore first and the mutex second.

### What is the readers-writers problem?

Several processes share data; readers only read it and writers modify it. Any number of readers may read at the same time, but a writer needs exclusive access, with no other writer or reader present. The problem is to enforce this while keeping either readers or writers from waiting forever.

### How can deadlock be avoided in the dining philosophers problem?

Break one of the deadlock conditions. Allow at most four philosophers to try to eat at once, make each philosopher pick up the lower-numbered chopstick first so no cycle can form, or let a philosopher pick up chopsticks only when both are free, checked inside a critical section or monitor.

### Does the first readers-writers solution cause starvation?

Yes. It gives readers preference: a writer can enter only when no reader is active, so a steady stream of overlapping readers keeps the read count above zero and the writer waits indefinitely. The second variant prefers writers and can starve readers instead; a fair variant serves readers and writers in arrival order.


---

## Module 6: Deadlocks in Operating Systems

*Original URL: https://codekairo.com/notes/operating-systems/deadlocks*

### Overview

Quick answer

### What is a deadlock in an operating system?

A deadlock is a state in which a set of processes are all blocked, each holding at least one resource and waiting for a resource held by another process in the set, so none of them can ever continue. It can occur only when four conditions hold together: mutual exclusion, hold and wait, no preemption and circular wait. Operating systems handle it by prevention, avoidance, detection and recovery, or by ignoring it.

- The system model
- The four necessary conditions
- The resource allocation graph
- Handling deadlocks
- Deadlock prevention
- Deadlock avoidance
- The Banker's algorithm
- Worked example: Banker's algorithm
- Deadlock detection and recovery
- Deadlock vs starvation vs livelock
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A deadlock is a standstill: a set of processes in which every process is waiting for something that only another process in the set can provide. Process P1 holds the printer and wants the scanner; P2 holds the scanner and wants the printer. Neither will release what it has, so both wait forever. Deadlocks come from ordinary, correct-looking code that grabs locks or devices in different orders, which is why every operating systems interview asks about them and many ask you to run the Banker's algorithm on paper.

### The system model

Resources come in types (CPU cycles, memory space, files, locks, printers), and each type has one or more identical instances . A process uses a resource in three steps: request it (waiting if it is not available), use it, and release it. Deadlock is a circle of processes stuck at the request step.

### The four necessary conditions

Coffman and his colleagues showed in 1971 that a deadlock can arise only if four conditions hold at the same time :

- Mutual exclusion. At least one resource is non-shareable: only one process can use it at a time.
- Hold and wait. A process holds at least one resource while waiting for others.
- No preemption. A resource cannot be taken from a process; it is released only voluntarily.
- Circular wait. There is a cycle P0 → P1 → … → Pn → P0 in which each process waits for a resource held by the next.

These are necessary conditions: remove any one and deadlock is impossible.

### The resource allocation graph

A resource allocation graph (RAG) shows the state at one moment. Processes are circles, resource types are rectangles with one dot per instance, a request edge P → R means P is waiting for R, and an assignment edge R → P means an instance of R is held by P.

- No cycle : no deadlock.
- A cycle, and every resource in it has one instance : deadlock.
- A cycle with multi-instance resources : possibly a deadlock, possibly not.

When every resource has a single instance, the graph can be collapsed into a wait-for graph with only processes: an edge Pi → Pj means Pi waits for a resource Pj holds. Then a deadlock exists if and only if the wait-for graph has a cycle.

P1 holds R2 and waits for R1; P2 holds R1 and waits for R2. Following the edges gives the cycle P1 → R1 → P2 → R2 → P1, and each resource has one instance, so both processes wait for ever.

- P1 holds R2 and waits for R1; P2 holds R1 and waits for R2. Following the edges gives the cycle P1 → R1 → P2 → R2 → P1, and each resource has one instance, so both processes wait for ever.
- With single instances, drop the resource boxes: P waits for Q whenever P requests something Q holds. The wait-for graph has the cycle P1 → P2 → P1, and a cycle there means deadlock, no more and no less.

With several instances per resource, a process outside the cycle can finish and free an instance, which breaks the cycle:

The cycle P1 → R1 → P3 → R2 → P1 is there, but R1 and R2 have two instances each, and P2 and P4 hold the others while waiting for nothing. No instance is free, so the detection algorithm looks for a process whose request can be met.

- The cycle P1 → R1 → P3 → R2 → P1 is there, but R1 and R2 have two instances each, and P2 and P4 hold the others while waiting for nothing. No instance is free, so the detection algorithm looks for a process whose request can be met.
- P2: it requests nothing, so it can run to the end and release its R1.
- P1: its request for R1 can be met, so it can run to the end and release its R2.
- P3: its request for R2 can be met, so it can run to the end and release its R1.
- P4: it requests nothing, so it can run to the end and release its R2. Every process finished, so there is no deadlock: with several instances a cycle is necessary but not sufficient.

### Handling deadlocks

General-purpose systems such as Linux and Windows take the last approach for user processes and leave deadlock handling to applications and databases.

### Deadlock prevention

Prevention attacks the conditions one at a time:

Ordering is the method used most in practice, and it is provably enough: a cycle would need some process to hold a higher-numbered resource while requesting a lower one, which the rule forbids.

Thread 1 locks A and thread 2 locks B, each the first lock its code asks for. Nothing has gone wrong yet: both locks were free.

- Thread 1 locks A and thread 2 locks B, each the first lock its code asks for. Nothing has gone wrong yet: both locks were free.
- Thread 1 now asks for B, held by thread 2, and thread 2 asks for A, held by thread 1. Each waits for the other: a cycle of two, and neither can ever continue.
- Now both lock A before B. Thread 1 gets A; thread 2 asks for A and waits — but it holds nothing, so no one can be waiting for it and no cycle can close.
- Thread 1 takes B, works and unlocks both; thread 2 then gets A and B in turn and finishes too. Locking in one global order removes circular wait, so this pair can never deadlock.

### Deadlock avoidance

Avoidance needs extra information: each process declares in advance the maximum number of instances of each resource type it may ever need. The OS then grants a request only if the resulting state is safe .

A state is safe if there is a safe sequence : an order of all processes such that each one's remaining need can be met by the currently available resources plus everything released by the processes before it. Then the OS can always finish every process in that order, so no deadlock can happen.

An unsafe state is not a deadlock; it only means the OS can no longer guarantee to avoid one. Avoidance stays out of unsafe states altogether.

For single-instance resources, avoidance can use the RAG with claim edges (dashed P → R edges for future requests): a request is granted only if turning its claim edge into an assignment edge creates no cycle. For multiple instances, it uses the Banker's algorithm.

### The Banker's algorithm

Named after a banker who never lends cash in a way that leaves him unable to satisfy all his customers' credit limits. For n processes and m resource types it keeps:

- Available[m] : free instances of each type.
- Max[n][m] : each process's declared maximum.
- Allocation[n][m] : what each process holds now.
- Need[n][m] = Max − Allocation : what each process may still request.

Safety algorithm.

- Set Work = Available and Finish[i] = false for every process.
- Find a process i with Finish[i] = false and Need[i] ≤ Work (in every resource type). If none exists, go to step 4.
- Pretend it runs to completion: Work = Work + Allocation[i], Finish[i] = true. Go to step 2.
- The state is safe if every Finish[i] is true.

Resource-request algorithm , when process i asks for Request[i]:

- If Request[i] > Need[i], it is an error: the process asked for more than it declared.
- If Request[i] > Available, the process must wait: the resources are not free.
- Otherwise pretend to grant it (Available −= Request, Allocation[i] += Request, Need[i] −= Request) and run the safety algorithm. If the new state is safe, grant the request; if not, restore the old state and make the process wait.

The safety check costs O(m × n²) per request.

### Worked example: Banker's algorithm

Five processes and three resource types with 8 instances of A, 6 of B and 7 of C.

Available = total − allocated = (8 6 7) − (6 4 4) = (2 2 3) .

Is the state safe? Each step picks the lowest-numbered unfinished process whose Need fits in Work:

Need = Max − Allocation, row by row, and Work starts as Available = total (8 6 7) − allocated = (2 2 3). The algorithm repeatedly looks for an unfinished process whose whole Need fits in Work.

- Need = Max − Allocation, row by row, and Work starts as Available = total (8 6 7) − allocated = (2 2 3). The algorithm repeatedly looks for an unfinished process whose whole Need fits in Work.
- P0 needs 3 of A but Work has 2. P1's Need (1 2 1) fits in Work (2 2 3): it can finish and release its Allocation, so Work becomes (4 2 4).
- P0's Need (3 2 2) fits in Work (4 2 4): it can finish and release its Allocation, so Work becomes (5 3 4).
- P2's Need (2 2 2) fits in Work (5 3 4): it can finish and release its Allocation, so Work becomes (6 5 5).
- P3's Need (1 2 2) fits in Work (6 5 5): it can finish and release its Allocation, so Work becomes (6 6 7).
- P4's Need (3 2 3) fits in Work (6 6 7): it can finish and release its Allocation, so Work becomes (8 6 7). Every process finished: the state is safe, and Work is back to the total.

Every process finishes, so the state is safe with the sequence P1, P0, P2, P3, P4. The final Work equals the total (8 6 7), a useful check. Other safe sequences exist too, such as P1, P3, P0, P2, P4; any one proves safety.

Request 1: P4 asks for (1 0 1). It is within P4's Need (3 2 3) and Available (2 2 3), and after pretending to grant it the state is still safe, so it is granted .

Request 2: P0 asks for (1 2 0), starting again from the original state. The resources are physically free, but after pretending to grant it Available would be (1 0 3) and no process's Need fits. The state would be unsafe , so the request is denied and P0 waits, even though the resources were there.

P4 asks for (1 0 1): within its Need and within Available. Pretend to grant it — Available becomes (1 2 2), P4's Need (2 2 2) — and rerun the safety check: P1, P0, P2, P3, P4 all finish, so the request is granted.

- P4 asks for (1 0 1): within its Need and within Available. Pretend to grant it — Available becomes (1 2 2), P4's Need (2 2 2) — and rerun the safety check: P1, P0, P2, P3, P4 all finish, so the request is granted.
- P0 asks for (1 2 0), also within its Need and Available. Pretend to grant it: Available becomes (1 0 3). Now no Need fits — P0 wants 2 of A with 1 free, and every other process wants B, which has none — so the state would be unsafe and P0 must wait.

Two more requests show the first two checks: P4 asking for (3 0 0) must wait, because only 2 of A are available; P1 asking for (2 0 0) is an error, because its Need for A is only 1.

This program runs the same checks and prints the same answers:

```
#
include
<cstdio>
#
include
<string>
#
include
<vector>
using
namespace
std
;
using
Matrix
=
vector
<
vector
<
int
>>
;
const
Matrix MAX
=
{
{
4
,
3
,
2
}
,
{
3
,
2
,
2
}
,
{
3
,
4
,
3
}
,
{
1
,
3
,
4
}
,
{
5
,
2
,
3
}
}
;
const
Matrix ALLOCATION
=
{
{
1
,
1
,
0
}
,
{
2
,
0
,
1
}
,
{
1
,
2
,
1
}
,
{
0
,
1
,
2
}
,
{
2
,
0
,
0
}
}
;
const
vector
<
int
>
AVAILABLE
=
{
2
,
2
,
3
}
;
const
int
N
=
5
,
M
=
3
;
bool
fits
(
const
vector
<
int
>
&
a
,
const
vector
<
int
>
&
b
)
{
for
(
int
j
=
0
;
j
<
M
;
j
++
)
if
(
a
[
j
]
>
b
[
j
]
)
return
false
;
return
true
;
}
vector
<
int
>
need
(
const
Matrix
&
alloc
,
int
i
)
{
vector
<
int
>
row
(
M
)
;
for
(
int
j
=
0
;
j
<
M
;
j
++
)
row
[
j
]
=
MAX
[
i
]
[
j
]
-
alloc
[
i
]
[
j
]
;
return
row
;
}
string
join
(
const
vector
<
int
>
&
v
)
{
string s
;
for
(
int
j
=
0
;
j
<
(
int
)
v
.
size
(
)
;
j
++
)
s
+=
(
j
?
" "
:
""
)
+
to_string
(
v
[
j
]
)
;
return
s
;
}
// Fills order with a safe sequence; returns false if the state is unsafe.
bool
safeSequence
(
const
Matrix
&
alloc
,
vector
<
int
>
work
,
string
&
order
)
{
vector
<
bool
>
finished
(
N
,
false
)
;
for
(
int
done
=
0
;
done
<
N
;
done
++
)
{
int
pick
=
-
1
;
// lowest-numbered unfinished process whose need fits in work
for
(
int
i
=
0
;
i
<
N
&&
pick
==
-
1
;
i
++
)
if
(
!
finished
[
i
]
&&
fits
(
need
(
alloc
,
i
)
,
work
)
)
pick
=
i
;
if
(
pick
==
-
1
)
return
false
;
for
(
int
j
=
0
;
j
<
M
;
j
++
)
work
[
j
]
+=
alloc
[
pick
]
[
j
]
;
// it finishes and releases
finished
[
pick
]
=
true
;
order
+=
(
done
?
" P"
:
"P"
)
+
to_string
(
pick
)
;
}
return
true
;
}
void
request
(
int
p
,
const
vector
<
int
>
&
req
)
{
string label
=
"P"
+
to_string
(
p
)
+
" requests "
+
join
(
req
)
+
": "
;
if
(
!
fits
(
req
,
need
(
ALLOCATION
,
p
)
)
)
{
printf
(
"%serror, more than its declared maximum\n"
,
label
.
c_str
(
)
)
;
return
;
}
if
(
!
fits
(
req
,
AVAILABLE
)
)
{
printf
(
"%smust wait, not enough available\n"
,
label
.
c_str
(
)
)
;
return
;
}
Matrix alloc
=
ALLOCATION
;
vector
<
int
>
avail
=
AVAILABLE
;
for
(
int
j
=
0
;
j
<
M
;
j
++
)
{
alloc
[
p
]
[
j
]
+=
req
[
j
]
;
avail
[
j
]
-=
req
[
j
]
;
}
string order
;
if
(
safeSequence
(
alloc
,
avail
,
order
)
)
printf
(
"%sgranted, safe sequence %s\n"
,
label
.
c_str
(
)
,
order
.
c_str
(
)
)
;
else
printf
(
"%sdenied, the state would be unsafe\n"
,
label
.
c_str
(
)
)
;
}
int
main
(
)
{
string rows
;
for
(
int
i
=
0
;
i
<
N
;
i
++
)
rows
+=
(
i
?
" | P"
:
"P"
)
+
to_string
(
i
)
+
" "
+
join
(
need
(
ALLOCATION
,
i
)
)
;
printf
(
"Need: %s\n"
,
rows
.
c_str
(
)
)
;
string order
;
if
(
safeSequence
(
ALLOCATION
,
AVAILABLE
,
order
)
)
printf
(
"Initial state is safe: %s\n"
,
order
.
c_str
(
)
)
;
else
printf
(
"Initial state is unsafe\n"
)
;
request
(
4
,
{
1
,
0
,
1
}
)
;
request
(
0
,
{
1
,
2
,
0
}
)
;
request
(
4
,
{
3
,
0
,
0
}
)
;
request
(
1
,
{
2
,
0
,
0
}
)
;
return
0
;
}
```

Output

```
Need: P0 3 2 2 | P1 1 2 1 | P2 2 2 2 | P3 1 2 2 | P4 3 2 3
Initial state is safe: P1 P0 P2 P3 P4
P4 requests 1 0 1: granted, safe sequence P1 P0 P2 P3 P4
P0 requests 1 2 0: denied, the state would be unsafe
P4 requests 3 0 0: must wait, not enough available
P1 requests 2 0 0: error, more than its declared maximum
```

Real systems rarely run it as is, since processes seldom know their maximum needs; it is the standard way to explain what "safe" means.

### Deadlock detection and recovery

Detection. With single-instance resources, keep a wait-for graph and search it for a cycle, which takes O(n²) for n processes. With multiple instances, run an algorithm shaped like the safety algorithm, using each process's current Request instead of its Need, and starting with Finish[i] = true for any process that holds nothing. Every process left unfinished at the end is deadlocked.

A tiny example with two resource types and nothing available, (0 0):

P2 requests nothing, so it can finish and release (1 1); then P0's request fits, then P1's. No deadlock. If P2 instead requested (1 0), no process's request would fit (0 0), and all three would be deadlocked.

Detection on every request is expensive, so systems run it periodically, or when CPU utilization drops because many processes are blocked.

Recovery has two options:

- Terminate processes : abort all deadlocked processes (simple, but loses all their work), or abort one at a time and rerun detection after each. The victim is chosen by cost: priority, how long it has run, how many resources it holds, and whether it is interactive.
- Preempt resources : take resources from a victim and give them to others. The victim must be rolled back to a safe earlier state, often a full restart. To avoid starving the same victim repeatedly, the cost should include how many times it has already been rolled back.

### Deadlock vs starvation vs livelock

A livelock is two people in a corridor who both step aside the same way, again and again: two threads that release and retry in step.

### Common mistakes

- Saying an unsafe state is a deadlock. It only means deadlock is possible; a safe state means it is impossible.
- Claiming any cycle in a RAG means deadlock. That is true only when each resource in the cycle has one instance.
- Forgetting the first two checks of the request algorithm: a request above Need is an error, and a request above Available simply waits.
- Computing Need as Max − Available instead of Max − Allocation.
- Thinking a safe sequence is unique. Several orders may work; finding one is enough.
- Calling the four conditions sufficient. They are necessary; with multi-instance resources they can all hold without a deadlock.

### Interview questions

What is a deadlock? Give a real example. A set of processes each holding a resource and waiting for one held by another in the set, so none can proceed. Two threads that lock mutexes A then B and B then A respectively, at the same moment, deadlock this way.

How can you prevent deadlock in a program that uses several locks? Impose a global order on the locks and always acquire them in that order, which makes circular wait impossible. Other options are acquiring all locks at once, or using try-lock with time-outs and releasing everything on failure.

What information does the Banker's algorithm need, and why is that a limitation? It needs each process's maximum demand for each resource type in advance, plus a fixed set of processes and resources. Real programs rarely know their maximum needs, and processes come and go, which is why the algorithm is mostly used for teaching.

What is the difference between deadlock avoidance and detection? Avoidance checks every request before granting it and keeps the system in safe states, so deadlock never happens. Detection grants requests freely, periodically checks whether a deadlock has formed, and then recovers by terminating processes or preempting resources.

Can a system be in an unsafe state and not deadlock? Yes. Unsafe means the OS cannot guarantee completion if every process asks for its declared maximum. If processes request less, or release resources early, they may all finish.

What is the difference between deadlock and starvation? In a deadlock no process in the set can ever proceed, because they wait on each other. In starvation the system as a whole progresses, but one process is repeatedly passed over; aging or fair queueing fixes it.

Next, read Memory Management , or work through the Operating Systems (Intermediate) skill test .

### What are the four necessary conditions for deadlock?

Mutual exclusion: a resource can be held by only one process at a time. Hold and wait: a process holds resources while waiting for more. No preemption: a resource cannot be taken away, only released voluntarily. Circular wait: a cycle of processes exists in which each waits for a resource held by the next. All four must hold at once.

### What is the difference between deadlock prevention and deadlock avoidance?

Prevention makes deadlock structurally impossible by ensuring at least one of the four conditions can never hold, for example by ordering resources so circular wait cannot form. Avoidance allows all four conditions but checks every request at run time, granting it only if the system stays in a safe state, as the Banker's algorithm does.

### What is a safe state in the Banker's algorithm?

A state is safe if there is at least one order, a safe sequence, in which every process can obtain its remaining maximum need from the available resources plus those released by the processes before it, and finish. A safe state cannot lead to deadlock. An unsafe state is not yet a deadlock, but it may lead to one.

### Does a cycle in a resource allocation graph always mean deadlock?

Only if every resource in the cycle has a single instance. With several instances per resource type, a cycle is necessary but not sufficient: a process outside the cycle may hold an instance, finish and release it, which breaks the cycle. With single instances, a cycle means deadlock.

### How do Linux and Windows handle deadlocks?

Neither prevents or avoids deadlocks between user processes. They take the so-called ostrich approach and leave it to applications, because the general mechanisms cost too much for a rare event. Inside the kernel, developers follow lock-ordering rules, and Linux has a debugging tool called lockdep that reports lock orders that could deadlock.


---

## Module 7: Inter-Process Communication

*Original URL: https://codekairo.com/notes/operating-systems/inter-process-communication*

### Overview

Quick answer

### What is inter-process communication in an operating system?

Inter-process communication (IPC) is the set of mechanisms an operating system provides for separate processes to exchange data and coordinate, since each process has its own protected address space. There are two basic models, shared memory and message passing. Common mechanisms are pipes, named pipes (FIFOs), message queues, shared memory segments, sockets and signals.

- Why processes communicate
- Shared memory vs message passing
- Pipes
- Named pipes (FIFOs)
- Message queues
- Shared memory segments
- Sockets
- Signals
- Comparing the mechanisms
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Processes are isolated on purpose: each has its own address space, so one cannot read or overwrite another's memory. But programs often need to cooperate. A shell connects ls to wc , a web server hands requests to worker processes, a browser's tabs talk to its main process. Inter-process communication (IPC) is the set of kernel-provided channels that let processes exchange data and signal each other without giving up that isolation. This note covers the two underlying models and the mechanisms built on them.

### Why processes communicate

Cooperating processes are used for information sharing (several programs reading one data set), computation speed-up (splitting work across processes on several cores), modularity (building a system from separate programs, as Unix pipelines and microservices do) and convenience (a user editing, compiling and printing at once). Threads of one process share memory already, so they need synchronization but not IPC; separate processes need both.

### Shared memory vs message passing

Every IPC mechanism follows one of two models.

In shared memory , the processes ask the kernel to map one region of physical memory into each of their address spaces. After that setup, they exchange data by ordinary reads and writes, with no kernel involvement, which makes it the fastest form of IPC. The processes themselves are responsible for not writing at the same time: a race on shared memory is exactly the problem of Process Synchronization , usually solved with a semaphore or mutex placed in the shared region.

In message passing , the processes call send(message) and receive(message) , and the kernel copies the message from the sender to the receiver. It costs a system call and a copy per message, but there is nothing to corrupt, it is easier to get right, and the same model works between machines.

Shared memory: the kernel maps one physical page into both address spaces once, and afterwards A stores and B loads with ordinary instructions. 3 messages cost no system calls and no copies, and nothing stops A and B colliding.

- Shared memory: the kernel maps one physical page into both address spaces once, and afterwards A stores and B loads with ordinary instructions. 3 messages cost no system calls and no copies, and nothing stops A and B colliding.
- Message passing: every send is a system call that copies the message into a kernel queue, and every receive a second one that copies it out. 3 messages cost 6 system calls and 6 copies, but the kernel orders and synchronizes them.

### Design choices in message passing

- Direct or indirect. In direct communication, a process names its partner: send(P, msg) . In indirect communication, messages go to a mailbox (also called a port), and any process sharing the mailbox can receive them.
- Blocking or non-blocking. A blocking (synchronous) send waits until the message is received; a non-blocking send returns at once. A blocking receive waits until a message arrives; a non-blocking receive returns a message or nothing. When both sides block, the exchange is a rendezvous .
- Buffering. The link's queue has zero capacity (the sender must wait for the receiver, a rendezvous), bounded capacity (the sender waits only when the queue is full) or, in theory, unbounded capacity (the sender never waits).

### Pipes

An ordinary pipe (anonymous pipe) is a one-way byte stream inside the kernel. pipe(fd) creates it and returns two file descriptors: fd[0] is the read end and fd[1] the write end. Since it has no name, other processes can reach it only by inheriting the descriptors, so pipes connect related processes , typically a parent and the child it forks.

```
#
include
<stdio.h>
#
include
<string.h>
#
include
<sys/wait.h>
#
include
<unistd.h>
int
main
(
void
)
{
int
fd
[
2
]
;
/* fd[0]: read end, fd[1]: write end */
if
(
pipe
(
fd
)
==
-
1
)
return
1
;
if
(
fork
(
)
==
0
)
{
/* child: the reader */
char
buf
[
32
]
;
close
(
fd
[
1
]
)
;
/* close the end it does not use */
ssize_t
n
=
read
(
fd
[
0
]
,
buf
,
sizeof
buf
-
1
)
;
buf
[
n
>
0
?
n
:
0
]
=
'\0'
;
printf
(
"child read: %s\n"
,
buf
)
;
return
0
;
}
close
(
fd
[
0
]
)
;
/* parent: the writer */
write
(
fd
[
1
]
,
"hello"
,
5
)
;
close
(
fd
[
1
]
)
;
/* the reader now sees end of file */
wait
(
NULL
)
;
return
0
;
}
```

pipe(fd) made a kernel buffer with a read end and a write end, and fork() gave the child both. Each process closed the end it does not use: the parent writes, the child reads. The buffer holds 8 bytes here, 64 KB on Linux.

- pipe(fd) made a kernel buffer with a read end and a write end, and fork() gave the child both. Each process closed the end it does not use: the parent writes, the child reads. The buffer holds 8 bytes here, 64 KB on Linux.
- The parent writes 11 bytes. 8 fit and the buffer is full, so the write blocks with 3 bytes still to go: a pipe is a bounded buffer and the kernel makes the writer wait.
- The child reads 5 bytes and gets "hello", the oldest bytes first. That frees 5 bytes of space.
- The writer wakes, puts its last 3 bytes in and the call returns 11. The child never sees where one write ended and the next began; a pipe carries only bytes.
- The parent closes the write end. No process holds it now, which the reader will notice only once the buffer is empty.
- The child asks for 16 bytes and gets the 6 that are there: a read returns what is available rather than waiting to fill its buffer.
- The buffer is empty and every write end is closed, so read returns 0, end of file. Had the child kept its own copy of fd[1] open, this read would block for ever.

Rules worth knowing:

- Each process should close the end it does not use . A reader sees end of file only when every write end is closed; a forgotten write end in the reader itself means it waits forever.
- Writing to a pipe whose read ends are all closed raises the signal SIGPIPE in the writer.
- The pipe has a fixed kernel buffer (64 KB by default on Linux). A writer blocks when it is full and a reader blocks when it is empty, which is the bounded buffer of Classic Synchronization Problems , done by the kernel.
- A shell pipeline such as ls | wc -l is two processes joined by an ordinary pipe: the shell creates the pipe, forks twice and connects one process's standard output to the other's standard input:

The shell calls pipe(): descriptors are handed out lowest free first, and 0, 1 and 2 are taken, so the read end is 3 and the write end 4.

- The shell calls pipe(): descriptors are handed out lowest free first, and 0, 1 and 2 are taken, so the read end is 3 and the write end 4.
- It forks twice. Each child starts with a copy of the shell's table, so both hold 3 and 4 as well as the terminal on 0, 1 and 2.
- Child 1 calls dup2(4, 1), child 2 dup2(3, 0); both close 3 and 4 and exec, and the shell closes its copies too. Now ls writes its standard output into the pipe and wc reads its standard input from it, and only ls holds a write end.

For two-way communication, use two pipes, one in each direction.

### Named pipes (FIFOs)

A named pipe , or FIFO , is a pipe with a name in the file system, created with mkfifo . Any process with permission can open the name, so FIFOs connect unrelated processes on the same machine. The name persists after the processes exit, until it is deleted, although the data inside does not. On Unix a FIFO is still one-way and byte-oriented, and opening one end blocks until the other end is opened too. Windows named pipes are different: they can be two-way and can even work between machines on a network.

```
mkfifo
/tmp/jobs
# create the FIFO
cat
/tmp/jobs
&
# a reader waits on it
echo
"build"
>
/tmp/jobs
# a writer in another process; the reader prints build
```

### Message queues

A message queue is a linked list of messages kept by the kernel. Unlike a pipe's byte stream, it preserves message boundaries : each receive returns one whole message. System V queues ( msgget , msgsnd , msgrcv ) give each message a type , so a receiver can ask for messages of one type; POSIX queues ( mq_open , mq_send , mq_receive ) give each a priority , and the highest-priority message is received first. A queue exists until it is explicitly removed, even if no process has it open, so a sender and a receiver need not run at the same time.

The same two writes go into a pipe and a message queue. The pipe keeps only bytes, so one read can return "abcd" with the seam gone; the queue keeps each message whole, and each receive returns exactly one.

- The same two writes go into a pipe and a message queue. The pipe keeps only bytes, so one read can return "abcd" with the seam gone; the queue keeps each message whole, and each receive returns exactly one.
- A POSIX queue also orders by priority: "stop" was sent second but has priority 5, so it is received first, and the two priority-1 messages follow in the order they were sent.

### Shared memory segments

With POSIX shared memory, one process creates a named object and both map it:

```
#
include
<fcntl.h>
#
include
<string.h>
#
include
<sys/mman.h>
#
include
<unistd.h>
int
main
(
void
)
{
int
fd
=
shm_open
(
"/demo"
,
O_CREAT
|
O_RDWR
,
0600
)
;
/* create or open by name */
ftruncate
(
fd
,
4096
)
;
/* set its size */
char
*
p
=
mmap
(
NULL
,
4096
,
PROT_READ
|
PROT_WRITE
,
MAP_SHARED
,
fd
,
0
)
;
strcpy
(
p
,
"hello from shared memory"
)
;
/* a plain memory write */
munmap
(
p
,
4096
)
;
close
(
fd
)
;
return
0
;
/* a reader maps "/demo" the same way; shm_unlink removes it */
}
```

Once mapped, the data never passes through the kernel again. The segment outlives the processes until shm_unlink (or System V's shmctl with IPC_RMID ) removes it.

### Sockets

A socket is an endpoint for two-way communication, identified on a network by an IP address and a port (for example 192.168.1.10:8080). Sockets are the only common IPC mechanism that works between machines , and they are the foundation of client-server systems: web servers, databases and chat applications all use them.

- Stream sockets (TCP) give a reliable, ordered byte stream over a connection.
- Datagram sockets (UDP) send independent messages that may be lost or reordered.
- Unix domain sockets use a file-system path instead of an address and work only on one machine, faster than TCP over the loopback interface; many local services, such as database servers, offer one.

A server calls socket , bind , listen and accept ; a client calls socket and connect ; both then send and recv :

The server makes a socket, descriptor 3, binds it to port 8080, marks it listening and calls accept(), which waits for a client.

- The server makes a socket, descriptor 3, binds it to port 8080, marks it listening and calls accept(), which waits for a client.
- The client makes its own socket and calls connect(). The kernels exchange the TCP handshake, and accept() returns a new descriptor, 4, for this one connection; 3 goes on listening for others.
- Both sides now send and recv on their connected descriptors, 3 and 4: a reliable two-way byte stream that works the same whether the two processes share a machine or not.

### Signals

A signal is an asynchronous notification sent to a process to tell it that an event happened. It carries no data beyond its number. Signals come from the kernel (an illegal memory access raises SIGSEGV), from other processes ( kill(pid, SIGTERM) ) or from the terminal (Ctrl+C sends SIGINT).

A process can accept the default action, ignore the signal, or install a handler that runs when it arrives:

```
#
include
<signal.h>
#
include
<stdio.h>
#
include
<unistd.h>
static
volatile
sig_atomic_t
stop
=
0
;
static
void
on_sigint
(
int
sig
)
{
(
void
)
sig
;
stop
=
1
;
}
/* keep handlers tiny */
int
main
(
void
)
{
struct
sigaction
sa
=
{
0
}
;
sa
.
sa_handler
=
on_sigint
;
sigaction
(
SIGINT
,
&
sa
,
NULL
)
;
/* Ctrl+C now runs on_sigint instead of killing us */
while
(
!
stop
)
pause
(
)
;
/* sleep until a signal arrives */
printf
(
"caught SIGINT, shutting down cleanly\n"
)
;
return
0
;
}
```

Standard signals are not queued: if the same signal arrives twice before it is handled, the process may see it once. Signals suit notifications such as "reload your configuration" or "a child exited", never bulk data.

### Common mistakes

- Saying shared memory needs no synchronization because it is fast. Speed comes precisely from the kernel staying out, so the processes must coordinate themselves.
- Saying an ordinary pipe can connect any two processes. Without a name, only processes that inherit its descriptors can use it.
- Forgetting to close unused pipe ends, so the reader never sees end of file.
- Treating a pipe as two-way. A Unix pipe is one-way; use two pipes or a socket pair.
- Claiming SIGKILL can be handled. SIGKILL and SIGSTOP can be neither caught nor ignored.
- Assuming message boundaries survive in a pipe or TCP stream. Two writes may arrive as one read; message queues and UDP keep boundaries.

### Interview questions

Why is shared memory faster than message passing? After the region is mapped, processes exchange data with ordinary memory instructions, without system calls or copies. Message passing enters the kernel and copies the data twice, from the sender into a kernel buffer and from there to the receiver, for every message.

How does a shell implement ls | wc -l ? It creates a pipe, forks a child for ls that makes the pipe's write end its standard output, and forks a child for wc -l that makes the read end its standard input. Each child closes the ends it does not use and calls exec on its program; the shell closes both ends and waits.

When would you use a socket instead of a pipe? When the processes may be on different machines, when they are unrelated and need a two-way channel, or when a server must accept connections from many clients. For two related processes on one machine, a pipe is simpler.

What happens when a process writes to a full pipe, or reads from an empty one? The writer blocks until a reader removes data, and the reader blocks until data arrives. If all write ends are closed, a read on an empty pipe returns end of file instead of blocking.

What is the difference between blocking and non-blocking message passing? A blocking send waits until the message is received and a blocking receive waits until a message arrives. Non-blocking calls return at once, with the message or with nothing, and the process checks again later.

Can signals be used to send data between processes? Not in any practical sense. A standard signal carries only its number and does not queue, so it is a notification mechanism. Data should go through a pipe, queue, socket or shared memory, with a signal at most announcing that it is there.

You have reached the end of the operating systems notes. Go back to the Operating Systems notes to revise any topic, then take the Operating Systems (Basic) and Operating Systems (Intermediate) skill tests.

### What are the two models of inter-process communication?

Shared memory, where processes map the same region of memory and read and write it directly, and message passing, where processes exchange messages through the kernel with send and receive operations. Shared memory is faster once set up but needs explicit synchronization; message passing is simpler, safer and works across machines.

### Which IPC mechanism is the fastest?

Shared memory, because after it is set up processes read and write the same physical pages with ordinary memory instructions and no system calls. Pipes, message queues and sockets copy data into the kernel and out again on every transfer. The cost of shared memory is that the processes must synchronize access themselves, for example with semaphores.

### What is the difference between a pipe and a named pipe?

An ordinary pipe has no name and exists only while processes hold its descriptors, so it can connect only related processes, typically a parent and its child that inherited it through fork. A named pipe, or FIFO, has a name in the file system, so any process with permission can open it, and the name persists until it is deleted.

### What is a signal in an operating system?

A signal is a small asynchronous notification sent to a process by the kernel or another process, identified only by its number, such as SIGINT when you press Ctrl+C or SIGKILL to force termination. The process can ignore it, run a handler, or take the default action, except for SIGKILL and SIGSTOP, which can be neither caught nor ignored.

### What is the difference between a message queue and a pipe?

A pipe carries an unstructured byte stream in one direction and its data disappears when the processes close it. A message queue carries discrete messages with boundaries, and often types or priorities, so a reader can pick particular messages, and the queue exists in the kernel until it is explicitly removed, even with no process attached.


---

## Module 8: Memory Management

*Original URL: https://codekairo.com/notes/operating-systems/memory-management*

### Overview

Quick answer

### What is memory management in an operating system?

Memory management is how the operating system shares physical memory among processes. It gives each process its own logical address space, maps those addresses to physical memory through the MMU, decides where each process is placed, protects processes from each other, and reclaims memory when they finish. The main techniques are contiguous allocation, paging and segmentation, with virtual memory built on top of paging.

- Logical and physical addresses
- Contiguous memory allocation
- First fit, best fit and worst fit
- Fragmentation and compaction
- Paging
- Segmentation
- Paging vs segmentation
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Every running process needs memory for its code, data, heap and stack, and physical memory is limited and shared. Memory management is the part of the operating system that decides which process gets which piece of RAM, translates the addresses programs use into real locations, keeps processes out of each other's memory, and takes memory back when a process exits. This note covers the techniques interviewers ask about, from simple contiguous allocation to paging and segmentation. How paging is used to run programs larger than RAM is in Virtual Memory and Demand Paging .

### Logical and physical addresses

- A logical address (also called a virtual address) is what the CPU generates while running a program: "variable x is at address 4500 in my space".
- A physical address is the actual location in RAM, as seen by the memory chips.

The memory management unit (MMU) , a hardware unit in the CPU, translates every logical address to a physical one on every memory access. The process only ever sees logical addresses, so the OS can place it anywhere in RAM and move it later.

The simplest MMU uses two registers. The relocation (base) register holds where the process starts in physical memory, and the limit register holds the size of its logical space. Every address is checked against the limit, then added to the base; here the base is 30000 and the limit 12000:

The CPU issues logical address 4500. The MMU checks it against the limit register: 4500 < 12000, so it is inside the process. It adds the base register: 30000 + 4500 = 34500.

- The CPU issues logical address 4500. The MMU checks it against the limit register: 4500 < 12000, so it is inside the process. It adds the base register: 30000 + 4500 = 34500.
- Logical address 0 is the first byte of the process: it passes the check and maps to 30000, the base itself. The process never learns where in memory it sits.
- Logical address 12500 fails the check, 12500 ≥ 12000: it lies outside the process's space, so no memory is touched and the MMU traps to the operating system with an addressing error.

Addresses can be bound to physical locations at compile time (fixed addresses, the program cannot move), at load time (fixed when the program is loaded), or at execution time (translated on every access by the MMU). Modern systems bind at execution time, which is what makes relocation, swapping and compaction possible.

Swapping moves a whole process out to a backing store on disk and back in later, so more processes can exist than fit in memory. Modern systems swap individual pages instead of whole processes.

### Contiguous memory allocation

In contiguous allocation each process occupies one continuous block of physical memory.

- Fixed partitions : memory is divided into partitions of set sizes in advance, one process per partition. Simple, but a small process in a large partition wastes the rest, and the number of partitions caps the number of processes.
- Variable partitions : each process gets exactly the size it asks for. Free memory becomes a set of holes scattered between processes. When a process asks for memory, the OS must choose a hole.

### First fit, best fit and worst fit

The three classic placement strategies:

- First fit : take the first hole, from the start of memory, that is big enough.
- Best fit : take the smallest hole that is big enough; this needs a search of the whole list unless it is kept sorted by size.
- Worst fit : take the largest hole, hoping the leftover stays useful.

Next fit is first fit that resumes searching where the last search stopped.

### Worked example

Free holes, in memory order: H1 = 150 KB, H2 = 400 KB, H3 = 250 KB, H4 = 600 KB, H5 = 300 KB. Requests arrive in the order 220 KB, 380 KB, 130 KB, 560 KB. The leftover part of a hole stays where it was as a smaller hole.

Five free holes sit between processes, and requests of 220, 380, 130, 560 KB arrive in that order. Each strategy places the same requests; the leftover of a hole stays where it was as a smaller hole.

- Five free holes sit between processes, and requests of 220, 380, 130, 560 KB arrive in that order. Each strategy places the same requests; the leftover of a hole stays where it was as a smaller hole.
- 220 KB: first fit stops at the first hole big enough, H2; best fit takes the smallest that fits, H3; worst fit the largest, H4.
- 380 KB goes to H4 under first fit, H2 under best fit and H2 under worst fit. Best fit's leftovers are already tiny: 20 and 30 KB.
- 130 KB goes to H1 under first fit, H1 under best fit and H4 under worst fit. Best fit's leftovers are already tiny: 20, 20 and 30 KB.
- 560 KB: first fit has 970 KB free in five holes but none of 560, so the request waits — external fragmentation. Best fit still has 600 KB in H4; worst fit's largest hole is 300 KB.

Best fit places all four requests here; first fit and worst fit cannot place the 560 KB one. Under first fit, 970 KB is still free when it fails (20 + 180 + 250 + 220 + 300), but no single hole holds 560 KB. That is external fragmentation in action. Do not over-learn this example, though: on other request sequences first fit wins, and best fit tends to leave tiny unusable slivers like the 20 KB holes above. Simulation studies generally find first fit and best fit similar in memory use, with first fit faster, and worst fit worse than both.

### Fragmentation and compaction

Internal: the last page holds only 2,308 bytes, so 1,788 bytes inside an allocated block are lost. External: 970 KB is free, more than the 560 KB request, but it is split into holes of at most 300 KB, so the request cannot be placed.

Compaction shuffles the processes in memory together so that all the holes merge into one. It needs execution-time binding, since a moved process only gets a new base register, and it is slow because large amounts of memory must be copied. The lasting cure is to stop needing contiguous space at all, which is what paging does.

### Paging

Paging lets a process's physical memory be non-contiguous. Physical memory is divided into fixed-size blocks called frames , the logical address space into blocks of the same size called pages , and a per-process page table records which frame holds each page. Any free frame can hold any page, so there is no external fragmentation.

### Address translation

If the page size is 2ⁿ bytes, the low n bits of a logical address are the offset d within the page and the remaining high bits are the page number p:

- page number p = logical address ÷ page size (integer division)
- offset d = logical address mod page size
- physical address = frame number × page size + offset

Worked example. The page size is 4 KB (4096 bytes, so n = 12) and part of a process's page table is:

Translate logical address 13000:

- p = 13000 ÷ 4096 = 3 (since 3 × 4096 = 12288), and d = 13000 − 12288 = 712.
- The page table maps page 3 to frame 6.
- Physical address = 6 × 4096 + 712 = 24576 + 712 = 25288 .

13000 in binary (its low 16 bits; the rest are 0). A 4 KB page is 2¹² bytes, so the low 12 bits are the offset, d = 712, and the bits above them the page number, p = 3.

- 13000 in binary (its low 16 bits; the rest are 0). A 4 KB page is 2¹² bytes, so the low 12 bits are the offset, d = 712, and the bits above them the page number, p = 3.
- The page number indexes the process's page table: entry 3 says page 3 is in frame 6. The offset is not looked up at all.
- The frame number replaces the page number and the offset is copied unchanged: 6 × 4096 + 712 = 25288, or 0x62C8. Translation is a table look-up and a bit substitution, with no addition.

Page table size. With 32-bit logical addresses and 4 KB pages, the page number has 32 − 12 = 20 bits, so the page table has 2²⁰ = 1,048,576 entries. At 4 bytes an entry that is 4 MB per process , which is why real systems use multi-level page tables.

Internal fragmentation. A process of 10,500 bytes with 4 KB pages needs 3 pages (10,500 ÷ 4096 = 2, remainder 2,308). The third page uses only 2,308 bytes, so 4096 − 2308 = 1,788 bytes are wasted. On average half a page per process is lost this way, which argues for small pages, while smaller pages mean bigger page tables.

### Hardware details

The page table lives in memory, located by the page-table base register (PTBR) . A plain implementation therefore needs two memory accesses per reference: one for the page-table entry and one for the data. A small, fast cache of recent translations, the translation look-aside buffer (TLB) , removes most of that cost; it is covered with its timing in the virtual memory note. Each page-table entry also carries protection bits (read, write, execute) and a valid-invalid bit that marks pages outside the process's address space. Paging also makes sharing easy: several processes' page tables can point to the same frames of read-only code, such as a shared library.

### Segmentation

Segmentation follows the programmer's view of a program as a collection of variable-size, logically separate parts: code, global data, heap, stack, each library. A logical address is a pair (segment number s, offset d) . The segment table gives each segment a base (where it starts in physical memory) and a limit (its length). The MMU checks d < limit, then adds the base.

Address (2, 300) names segment 2, data, and offset 300. The segment table gives its base 4000 and limit 800; 300 < 800, so the physical address is 4000 + 300 = 4300.

- Address (2, 300) names segment 2, data, and offset 300. The segment table gives its base 4000 and limit 800; 300 < 800, so the physical address is 4000 + 300 = 4300.
- (0, 1199) is the last byte of the code segment: 1199 < 1200 passes, by one, and maps to 3199. An offset equal to the limit would already be outside.
- (1, 520) asks for byte 520 of the stack segment, which is only 500 bytes long. 520 ≥ 500, so the MMU traps before 6520 is touched: a segmentation fault.

Because segments are meaningful units, protection fits naturally: code read-only and executable, data read-write, and a whole segment can be shared. The cost is that segments have variable sizes, so allocating them brings back external fragmentation . Systems that combined the two, such as 32-bit x86, split memory into segments and then paged each segment; 64-bit x86 keeps segmentation only in vestigial form and relies on paging.

### Common mistakes

- Saying paging has no fragmentation at all. It has no external fragmentation, but the last page of each process wastes some space internally.
- Using 1 KB = 1000 bytes in address arithmetic. Page sizes are powers of two: 4 KB is 4096 bytes.
- Forgetting the limit check in segmentation, or comparing with ≤ instead of <: an offset equal to the limit is already outside the segment.
- Treating best fit as always best. It leaves the smallest leftovers, which are often too small to use.
- Mixing up pages and frames: pages are logical, frames are physical, and they are the same size.
- Computing the page table size from the physical memory size; the number of entries depends on the logical address space.

### Interview questions

What does the MMU do? It translates every logical address the CPU generates into a physical address, at run time, using base and limit registers or page and segment tables. It also enforces protection, raising a trap when a process touches memory outside its space or breaks a page's permissions.

Why does paging eliminate external fragmentation? Every frame is the same size and any free frame can hold any page, so a process never needs a contiguous run of free memory. Any free frame is usable, so free memory is never stranded in holes too small to use.

How do you find the number of bits for the page number and offset? The offset needs log₂(page size) bits, such as 12 bits for 4 KB pages. The page number takes the remaining bits of the logical address, such as 20 bits of a 32-bit address, giving 2²⁰ pages.

What is the trade-off in choosing a page size? Small pages waste less to internal fragmentation and track memory use more finely, but need larger page tables and more TLB entries. Large pages mean smaller tables and fewer TLB misses but more internal fragmentation.

Why is segmentation said to match the user's view of memory? Programmers think of a program as code, data, a stack and libraries, each of a different size. Segmentation gives each of those its own segment with its own length and permissions, instead of slicing everything into equal pages.

What is the difference between swapping and paging? Classic swapping moves an entire process between memory and disk. Paging moves individual pages, so only the parts of a process actually needed are in memory.

Next, read Virtual Memory and Demand Paging , or check yourself with the Operating Systems (Basic) skill test .

### What is the difference between a logical and a physical address?

A logical address, also called a virtual address, is generated by the CPU while a program runs and is relative to the process's own address space. A physical address is the actual location in RAM. The memory management unit translates every logical address into a physical one at run time, so a program never sees where it really is in memory.

### What is the difference between internal and external fragmentation?

Internal fragmentation is wasted space inside an allocated block, because the block is larger than requested, such as the unused end of a process's last page. External fragmentation is free memory split into many small holes between allocated blocks, so the total free space is enough for a request but no single hole is. Paging removes external fragmentation but keeps internal.

### Which is better, first fit, best fit or worst fit?

First fit and best fit both use memory better than worst fit, and first fit is usually fastest because it stops searching at the first hole that fits. Best fit leaves the smallest leftovers, which may be too small to use. No strategy wins on every request sequence; simulations generally favour first fit for speed and match it with best fit on utilization.

### How is a logical address translated in paging?

The logical address is split into a page number and an offset. With a page size of 2 to the power n, the low n bits are the offset and the remaining high bits are the page number. The page number indexes the page table to get a frame number, and the physical address is the frame number times the page size plus the offset.

### What is the difference between paging and segmentation?

Paging divides memory into fixed-size pages and frames that are invisible to the programmer, so there is no external fragmentation but some internal fragmentation. Segmentation divides a program into variable-size logical units such as code, stack and data, matching the programmer's view and making protection and sharing natural, but it suffers from external fragmentation.

### What is compaction in memory management?

Compaction moves the processes in memory so that all free holes merge into one large block, curing external fragmentation. It is possible only when addresses are bound at execution time, so that a moved process just gets a new base register value, and it is expensive because large amounts of memory must be copied.


---

## Module 9: Virtual Memory and Demand Paging

*Original URL: https://codekairo.com/notes/operating-systems/virtual-memory*

### Overview

Quick answer

### What is virtual memory in an operating system?

Virtual memory is a technique that separates a process's logical address space from physical memory, so a program can run with only part of it in RAM. Pages are loaded on demand when first touched, and a page fault brings in a missing page from disk. It lets programs be larger than physical memory, lets more processes run at once, and makes sharing and copy-on-write easy.

- Why virtual memory
- Demand paging
- The TLB and effective access time
- Multi-level page tables
- Thrashing
- The working-set model
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Virtual memory lets a process behave as if it had a large, private, contiguous memory of its own, while the operating system keeps only the parts currently in use in physical RAM and the rest on disk. It is built on paging, explained in Memory Management : because pages can live in any frame, they can also live in no frame at all until needed. This note covers how missing pages are brought in, what that costs, how the TLB and multi-level page tables keep translation fast and small, and what happens when memory runs short: thrashing.

### Why virtual memory

Programs rarely need all their code and data at once. Error handlers, rarely used features and oversized arrays sit untouched. Virtual memory exploits this:

- A program can be larger than physical memory .
- More processes fit in memory at once, raising CPU utilization and throughput.
- Programs start faster, because less has to be read from disk.
- Sharing is cheap: shared libraries are mapped into many processes, and after fork() parent and child share pages copy-on-write until one of them writes.
- Files can be memory-mapped , read and written as ordinary memory.

It works because of locality of reference : in any short period a program touches a small set of pages (a loop's code, the array it is scanning, the top of the stack), and that set changes slowly.

### Demand paging

With demand paging , a page is loaded only when it is first referenced. Each page-table entry has a valid-invalid bit : valid means the page is in memory, invalid means it is either not part of the process or not loaded yet. Pure demand paging starts a process with no pages at all and faults in every one as it is touched.

### Handling a page fault

When a process touches a page marked invalid, the MMU raises a page fault trap and the OS brings the page in:

The process executes load M, and M lies in page 3. The MMU finds entry 3 marked invalid (i): the page is not in memory.

- The process executes load M, and M lies in page 3. The MMU finds entry 3 marked invalid (i): the page is not in memory.
- The invalid bit raises a page fault, a trap into the operating system. It checks the process's tables: page 3 is a legal page kept on the backing store, so this is not a segmentation fault.
- The OS takes a free frame, frame 5. With none free, a replacement policy would choose a victim, written back to disk first if its dirty bit is set.
- It schedules a disk read of page 3 into frame 5. The read takes milliseconds, so the process waits and the CPU runs another process meanwhile.
- When the read completes, the OS writes frame 5 into entry 3 and sets its bit to valid (v).
- The instruction that faulted is restarted from the beginning. This time entry 3 is valid, the translation gives frame 5, and the load completes as if nothing had happened.

If no frame is free, a replacement policy picks a victim frame first, and the victim is written back to disk only if it has been modified (its dirty bit is set). A fault that needs a disk read is a major fault; one resolved without I/O, for example a page already in memory for another process, is a minor fault. Choosing the victim is the subject of Page Replacement Algorithms .

### Cost of a page fault

Let p be the page-fault rate (0 ≤ p ≤ 1). Then:

Effective access time = (1 − p) × memory access time + p × page-fault service time

Take a memory access of 200 ns and a page-fault service time of 8 ms (8,000,000 ns), dominated by the disk:

- EAT = (1 − p) × 200 + p × 8,000,000 = 200 + 7,999,800 × p ns.
- With one fault in every 1,000 accesses (p = 0.001): EAT = 200 + 7,999.8 = 8,199.8 ns , about 41 times slower than memory.
- To keep the slowdown under 10%, EAT must stay below 220 ns: 7,999,800 × p < 20, so p < 0.0000025, fewer than one fault in about 400,000 accesses .

The lesson interviewers want: the fault rate must be extremely low, so the replacement policy and the number of frames per process matter enormously.

### The TLB and effective access time

The page table lives in memory, so a naive translation costs one memory access for the page-table entry and another for the data. The translation look-aside buffer (TLB) is a small, fast associative cache, typically tens to a few thousand entries, holding recent page → frame translations. On a TLB hit the frame number comes straight from the TLB; on a miss the hardware or the OS walks the page table and then caches the translation. Entries are tagged with an address-space identifier on many CPUs, so a context switch need not flush the whole TLB.

With TLB lookup time t, memory access time m and hit ratio h, for a single-level page table:

EAT = h × (t + m) + (1 − h) × (t + 2m)

Page 2 is in the TLB, a hit: the frame number, 6, comes straight out of the TLB and only the data itself is read from memory, 20 + 100 = 120 ns.

- Page 2 is in the TLB, a hit: the frame number, 6, comes straight out of the TLB and only the data itself is read from memory, 20 + 100 = 120 ns.
- Page 7 is not in the TLB, a miss. The page table, itself in memory, is read for frame 3 (one access), the translation replaces page 5, the least recently used entry, and then the data is read: 220 ns.
- On average, with 98% of lookups hitting, an access costs 122 ns: within 22% of a bare memory access, against 200 ns with no TLB at all.

Worked example , with t = 20 ns and m = 100 ns, so a hit costs 120 ns and a miss 220 ns:

A 98% hit ratio brings the cost within 22% of a bare memory access, and the deeper page table hardly matters because misses are rare. Some textbooks treat the TLB lookup as free (t = 0); then the 0.80 case is 0.80 × 100 + 0.20 × 200 = 120 ns. Read which convention a question uses.

### Multi-level page tables

A 32-bit address space with 4 KB pages needs 2²⁰ page-table entries; at 4 bytes each that is 4 MB per process , nearly all describing addresses the process never uses. The fix is to page the page table itself.

In a two-level scheme, the 32-bit address splits into 10 + 10 + 12 bits: the top 10 index the outer table, the next 10 an inner table, and the low 12 are the offset in the page.

The 32-bit address splits into three fields: the top 10 bits index the outer table (p1 = 1), the next 10 an inner table (p2 = 3), and the low 12 are the offset in the 4 KB page (d = 0xABC = 2748).

- The 32-bit address splits into three fields: the top 10 bits index the outer table (p1 = 1), the next 10 an inner table (p2 = 3), and the low 12 are the offset in the 4 KB page (d = 0xABC = 2748).
- Entry 1 of the outer table points to an inner table. The outer table has 1,024 entries of 4 bytes, so it fills exactly one 4 KB page.
- Entry 3 of that inner table holds the frame, 9; the offset is appended unchanged, giving 39612. On a TLB miss that walk costs one memory access per level.
- The saving: an inner table exists only where the process has memory. 8 MB of code and data use outer entries 0 and 1, the 4 MB stack entry 1023, so 3 inner tables plus the outer one cost 16 KB instead of 4 MB.

The outer table is 1,024 × 4 B = 4 KB, and each inner table is also 4 KB and maps 4 MB of address space. Inner tables are allocated only for regions in use. A process with 8 MB of code and data at the bottom of its space and a 4 MB stack at the top needs one outer table and 2 + 1 = 3 inner tables: 4 × 4 KB = 16 KB instead of 4 MB.

The price is one memory access per level on a TLB miss. x86-64 uses four levels of 9 bits each over 48-bit virtual addresses (4 × 9 + 12 = 48), and newer processors support five levels for 57-bit addresses, which is only practical because TLB hit ratios are high. Alternatives for very large address spaces are hashed page tables and inverted page tables , which keep one entry per physical frame instead of per virtual page.

### Thrashing

If a process does not have enough frames for the pages it is actively using, it faults, evicts a page it needs again moments later, faults again, and so on. When the system as a whole spends more time servicing page faults than executing, it is thrashing .

The classic way it starts:

- Processes have too few frames, so the page-fault rate rises.
- They queue for the paging disk, so CPU utilization drops.
- The long-term scheduler sees an idle CPU and admits more processes.
- Each new process takes frames from the others, so the fault rate rises further.

Plotted against the degree of multiprogramming, CPU utilization climbs, peaks, then falls off sharply: that cliff is thrashing. The cure is to give each process the frames it needs, and to reduce the number of processes in memory, by suspending some, when there are not enough frames for all. Local replacement , where a process may evict only its own pages, keeps one thrashing process from dragging others down, though it does not cure that process.

### The working-set model

The working set WS(t, Δ) of a process is the set of distinct pages it referenced in its last Δ references, the working-set window . It approximates the process's current locality.

Worked example with Δ = 4 and this reference string:

At time 4 the window holds 1 2 3 1: the working set is {1, 2, 3}, size 3. The process is still in its first locality, pages 1 to 3.

- At time 4 the window holds 1 2 3 1: the working set is {1, 2, 3}, size 3. The process is still in its first locality, pages 1 to 3.
- At time 5 the window holds 2 3 1 2: the working set is {1, 2, 3}, size 3.
- At time 6 the window holds 3 1 2 4: the working set is {1, 2, 3, 4}, size 4. Page 4 enters, so the set grows while the old locality is still in the window.
- At time 7 the window holds 1 2 4 4: the working set is {1, 2, 4}, size 3. It shrinks: page 3 fell out of the window.
- At time 8 the window holds 2 4 4 4: the working set is {2, 4}, size 2. It shrinks: page 1 fell out of the window.
- At time 9 the window holds 4 4 4 5: the working set is {4, 5}, size 2. Page 5 enters as page 2 leaves: the locality is moving.
- At time 10 the window holds 4 4 5 5: the working set is {4, 5}, size 2.
- At time 11 the window holds 4 5 5 4: the working set is {4, 5}, size 2.
- At time 12 the window holds 5 5 4 5: the working set is {4, 5}, size 2. Frames for these pages are all it needs now.

The working set shrinks and moves as the process settles into a new locality. If the window is too small it misses part of the locality; if too large it spans several; an infinite window is every page ever touched.

Let WSSᵢ be the working-set size of process i and D = Σ WSSᵢ the total demand for frames. If D exceeds the number of available frames, some process lacks its working set and thrashing follows, so the OS suspends a process and gives its frames to the others. Keeping exact working sets is expensive, so systems approximate them with reference bits sampled on a timer.

A more direct control is page-fault frequency (PFF) : set an upper and a lower bound on each process's fault rate. Above the upper bound, give the process more frames; below the lower bound, take some away; if no frames are free, suspend a process.

### Common mistakes

- Treating every page fault as an error. Most are normal demand paging; only an access to an address outside the process ends in a segmentation fault.
- Forgetting the dirty bit: a clean victim page need not be written back, which halves the cost of that fault.
- Writing EAT with a TLB miss costing t + m instead of t + 2m for a single-level page table: a miss reads the page table and then the data.
- Saying multi-level page tables make translation faster. They save memory; a TLB miss gets slower, one access per level.
- Saying more processes always means better CPU utilization. Past the thrashing point, utilization falls.
- Confusing the working set with the resident set: the working set is what the process recently used, the resident set is what happens to be in memory.

### Interview questions

What are the steps in handling a page fault? Trap to the OS, check the reference is legal, find a free frame or evict a victim (writing it back if dirty), read the page from disk while another process runs, update the page table and valid bit, then restart the faulting instruction.

How does the TLB reduce effective memory access time? It caches recent page-to-frame translations, so a hit skips the page-table read. With a 98% hit ratio, a 20 ns TLB and 100 ns memory, the average access is 122 ns instead of 200 ns without a TLB.

What causes thrashing and how do you stop it? The total working sets of the running processes exceed physical memory, so processes keep stealing each other's active pages. Stop it by reducing the degree of multiprogramming, using the working-set model or page-fault frequency to give each process enough frames, and using local replacement.

What is the difference between virtual memory and physical memory? Physical memory is the installed RAM. Virtual memory is the address space each process sees, which can be larger than RAM; it is mapped onto RAM page by page, with the rest kept on disk.

What is copy-on-write? After fork() , parent and child share the same physical pages, marked read-only. Only when one of them writes to a page does the kernel copy that page, so a child that immediately calls exec() copies almost nothing.

Why is the effective access time so sensitive to the page-fault rate? In the textbook figures a fault costs 8 ms against 200 ns for a memory access, 40,000 times more, so even one fault in a thousand accesses makes memory about 41 times slower on average. Only fault rates of a few per million accesses keep the overhead small.

Next, read Page Replacement Algorithms , or test yourself with the Operating Systems (Intermediate) skill test .

### What is demand paging?

Demand paging loads a page into memory only when the process first accesses it, instead of loading the whole program at start. Pages never used are never loaded, which saves memory and start-up time. A reference to a page that is not in memory causes a page fault, and the operating system then reads the page from disk.

### What is a page fault?

A page fault is the trap raised when a process accesses a page whose page-table entry is marked invalid, usually because the page is not in physical memory. The operating system checks the access is legal, finds a free frame, reads the page in from disk, updates the page table and restarts the instruction. An illegal access instead ends in a segmentation fault.

### What is a TLB and why is it needed?

The translation look-aside buffer is a small, fast hardware cache of recent page-number to frame-number translations. Without it, every memory reference would need an extra memory access to read the page table, doubling access time. With a high hit ratio, most translations come from the TLB and the average access time stays close to a single memory access.

### What is thrashing in an operating system?

Thrashing is when processes spend more time paging than executing, because they do not have enough frames for the pages they are actively using. Each fault evicts a page another process needs soon, so faults cascade, CPU utilization collapses and the disk is saturated. It is cured by reducing the number of processes in memory or giving each enough frames for its working set.

### What is the working set model?

The working set of a process is the set of pages it referenced in its most recent window of delta references, an approximation of its current locality. The operating system tries to keep each process's working set in memory and, if the sum of all working set sizes exceeds the number of frames, suspends a process to prevent thrashing.

### Why are multi-level page tables used?

A single-level page table for a 32-bit address space with 4 KB pages has a million entries, about 4 MB per process, mostly describing unused addresses. A multi-level table pages the page table itself: only the parts covering addresses the process actually uses are allocated, which cuts the memory needed to a few kilobytes for a small process.


---

## Module 10: Page Replacement Algorithms

*Original URL: https://codekairo.com/notes/operating-systems/page-replacement-algorithms*

### Overview

Quick answer

### What is a page replacement algorithm?

A page replacement algorithm decides which page in memory to evict when a page fault occurs and no frame is free. The goal is the fewest page faults. FIFO evicts the oldest loaded page, Optimal evicts the page not needed for the longest time, LRU evicts the page unused for the longest time, and the clock algorithm approximates LRU cheaply with reference bits.

- The setup
- FIFO (First-In, First-Out)
- Optimal (OPT or MIN)
- LRU (Least Recently Used)
- LRU approximations: second chance and clock
- Belady's anomaly
- Simulating the algorithms
- FIFO vs LRU vs Optimal vs clock
- Common mistakes
- Interview questions
- Common questions
- Test yourself

When a page fault occurs and every frame is in use, the operating system must evict a page to make room. Which page it picks decides how soon the next fault comes, and with a page fault costing thousands of times more than a memory access, that choice dominates performance (the arithmetic is in Virtual Memory and Demand Paging ). Page replacement questions are almost always the same exercise: a reference string, a number of frames, and "how many page faults?". This note works one string through every algorithm, then shows Belady's anomaly.

### The setup

A reference string is the sequence of page numbers a process accesses. Repeated references to the same page in a row are collapsed, since only the first can fault. A page fault happens whenever the referenced page is not in a frame; the first reference to each page always faults (a compulsory or cold fault), including while frames are still empty. Some books count only the faults after the frames fill up, so always state which you mean: here every fault counts.

Throughout this note:

- Reference string: 2 3 2 1 5 2 4 5 3 2 5 2 (12 references, 5 distinct pages)
- Frames: 3 , initially empty

The figures draw what you would write on paper: one column per reference, the frame contents after it in fixed slots (a new page takes the slot of the page it evicts), an F under every fault and the evicted page under that.

### FIFO (First-In, First-Out)

Evict the page that has been in memory the longest , regardless of how often it is used. It needs only a queue of pages in load order.

Step 1: page 2 is not in memory, a compulsory fault. It goes into the empty frame 1.

- Step 1: page 2 is not in memory, a compulsory fault. It goes into the empty frame 1.
- Step 2: page 3 is not in memory, a compulsory fault. It goes into the empty frame 2.
- Step 3: page 2 is already in frame 1, a hit; FIFO ignores hits, so nothing changes.
- Step 4: page 1 is not in memory, a compulsory fault. It goes into the empty frame 3.
- Step 5: page 5 faults and every frame is full. FIFO evicts page 2, loaded at step 1, the oldest, and 5 takes frame 1.
- Step 6: page 2 faults and every frame is full. FIFO evicts page 3, loaded at step 2, the oldest, and 2 takes frame 2.
- Step 7: page 4 faults and every frame is full. FIFO evicts page 1, loaded at step 4, the oldest, and 4 takes frame 3.
- Step 8: page 5 is already in frame 1, a hit; FIFO ignores hits, so nothing changes.
- Step 9: page 3 faults and every frame is full. FIFO evicts page 5, loaded at step 5, the oldest, and 3 takes frame 1.
- Step 10: page 2 is already in frame 2, a hit; FIFO ignores hits, so nothing changes.
- Step 11: page 5 faults and every frame is full. FIFO evicts page 2, loaded at step 6, the oldest, and 5 takes frame 2.
- Step 12: page 2 faults and every frame is full. FIFO evicts page 4, loaded at step 7, the oldest, and 2 takes frame 3. FIFO ends with 9 faults and 3 hits.

FIFO: 9 faults, 3 hits. Step 5 shows the weakness: page 2 is evicted because it was loaded first, even though it was used two steps earlier and is needed again at once.

### Optimal (OPT or MIN)

Evict the page that will not be used for the longest time in the future. It gives the lowest possible number of faults for any reference string and number of frames, but it needs the future, so no operating system can run it. It is the yardstick other algorithms are measured against.

Step 1: page 2 is not in memory, a compulsory fault. It goes into the empty frame 1.

- Step 1: page 2 is not in memory, a compulsory fault. It goes into the empty frame 1.
- Step 2: page 3 is not in memory, a compulsory fault. It goes into the empty frame 2.
- Step 3: page 2 is already in frame 1, a hit; nothing needs to change.
- Step 4: page 1 is not in memory, a compulsory fault. It goes into the empty frame 3.
- Step 5: page 5 faults and every frame is full. Optimal evicts page 1, never used again, and 5 takes frame 3.
- Step 6: page 2 is already in frame 1, a hit; nothing needs to change.
- Step 7: page 4 faults and every frame is full. Optimal evicts page 2, next used at step 10, the farthest away, and 4 takes frame 1.
- Step 8: page 5 is already in frame 3, a hit; nothing needs to change.
- Step 9: page 3 is already in frame 2, a hit; nothing needs to change.
- Step 10: page 2 faults and every frame is full. Optimal evicts page 3, never used again; neither is 4, and the tie goes to the page loaded first, and 2 takes frame 2.
- Step 11: page 5 is already in frame 3, a hit; nothing needs to change.
- Step 12: page 2 is already in frame 2, a hit; nothing needs to change. Optimal ends with 6 faults and 6 hits.

Optimal: 6 faults, 6 hits. At step 7 the next uses are page 2 at step 10, page 3 at step 9 and page 5 at step 8, so 2 goes. At step 10 neither 4 nor 3 is used again; either may go, and the count is the same.

### LRU (Least Recently Used)

Evict the page that has not been used for the longest time in the past. It uses the recent past as a prediction of the near future, which is what locality of reference suggests.

Step 1: page 2 is not in memory, a compulsory fault. It goes into the empty frame 1.

- Step 1: page 2 is not in memory, a compulsory fault. It goes into the empty frame 1.
- Step 2: page 3 is not in memory, a compulsory fault. It goes into the empty frame 2.
- Step 3: page 2 is already in frame 1, a hit; it becomes the most recently used page.
- Step 4: page 1 is not in memory, a compulsory fault. It goes into the empty frame 3.
- Step 5: page 5 faults and every frame is full. LRU evicts page 3, last used at step 2, the longest ago, and 5 takes frame 2.
- Step 6: page 2 is already in frame 1, a hit; it becomes the most recently used page.
- Step 7: page 4 faults and every frame is full. LRU evicts page 1, last used at step 4, the longest ago, and 4 takes frame 3.
- Step 8: page 5 is already in frame 2, a hit; it becomes the most recently used page.
- Step 9: page 3 faults and every frame is full. LRU evicts page 2, last used at step 6, the longest ago, and 3 takes frame 1.
- Step 10: page 2 faults and every frame is full. LRU evicts page 4, last used at step 7, the longest ago, and 2 takes frame 3.
- Step 11: page 5 is already in frame 2, a hit; it becomes the most recently used page.
- Step 12: page 2 is already in frame 3, a hit; it becomes the most recently used page. LRU ends with 7 faults and 5 hits.

LRU: 7 faults, 5 hits. At step 5, LRU keeps page 2 because it was just used, which FIFO did not.

Implementing exact LRU needs help on every memory access: either a counter (a timestamp stored in the page-table entry at each reference, with the smallest timestamp evicted) or a stack of page numbers where a referenced page moves to the top and the bottom is the victim. Both are too expensive in software, so real systems approximate LRU.

### LRU approximations: second chance and clock

Most hardware sets a reference bit in a page's entry whenever the page is accessed. The OS can clear these bits and later see which pages were used since.

- Additional-reference-bits (aging). Keep a byte per page. On every timer interrupt, shift the byte right and copy the reference bit into its top bit, then clear the reference bit. The page with the smallest byte, read as a number, is the least recently used, approximately.
- Second chance. FIFO, but when the oldest page's reference bit is 1, clear it and move on instead of evicting it. A page used since the last pass survives one more round.
- Clock. Second chance with the pages in a circular list and a hand pointing at the next candidate. On a fault, the hand clears 1 bits and advances until it finds a 0 bit, evicts that page, loads the new one with its bit set to 1, and moves one step on. On a hit, the page's bit is set to 1.

The clock algorithm on the same string and three frames, with each page's reference bit beside it and the hand where it points after the step:

Step 1: page 2 faults and the hand's slot 1 is empty, so it loads there with bit 1 and the hand steps on to slot 2.

- Step 1: page 2 faults and the hand's slot 1 is empty, so it loads there with bit 1 and the hand steps on to slot 2.
- Step 2: page 3 faults and the hand's slot 2 is empty, so it loads there with bit 1 and the hand steps on to slot 3.
- Step 3: page 2 is in slot 1, a hit. The hardware sets its reference bit to 1; the hand does not move.
- Step 4: page 1 faults and the hand's slot 3 is empty, so it loads there with bit 1 and the hand steps on to slot 1.
- Step 5: page 5 faults with every bit 1. The hand sweeps the whole circle clearing bits (2, 3, 1), comes back to 2 and evicts it: for this fault the clock is plain FIFO.
- Step 6: page 2 faults. The hand points at 3, whose bit is 0, so 3 is evicted at once and 2 loads with bit 1.
- Step 7: page 4 faults. The hand points at 1, whose bit is 0, so 1 is evicted at once and 4 loads with bit 1.
- Step 8: page 5 is in slot 1, a hit. The hardware sets its reference bit to 1; the hand does not move.
- Step 9: page 3 faults with every bit 1. The hand sweeps the whole circle clearing bits (5, 2, 4), comes back to 5 and evicts it: for this fault the clock is plain FIFO.
- Step 10: page 2 is in slot 2, a hit. The hardware sets its reference bit to 1; the hand does not move.
- Step 11: page 5 faults. Page 2 had bit 1, so the hand clears it and moves on, a second chance; 4 has bit 0 and is evicted.
- Step 12: page 2 is in slot 2, a hit. The hardware sets its reference bit to 1; the hand does not move. The clock ends with 8 faults.

Clock: 8 faults , between FIFO's 9 and LRU's 7. When every bit is 1, as at steps 5 and 9, the clock sweeps the whole circle and degenerates into FIFO for that fault.

The enhanced second-chance algorithm also uses the modify (dirty) bit and prefers to evict, in order: not referenced and not modified (0, 0), then (0, 1), then (1, 0), then (1, 1), because a clean page can be dropped without writing it to disk. Linux approximates LRU with active and inactive page lists, in the same spirit.

Two counting policies also appear in textbooks: LFU (evict the least frequently used page) and MFU (evict the most frequently used, on the theory that a low count means a page was just loaded). Neither is common, as both approximate Optimal poorly.

### Belady's anomaly

You would expect more frames to mean fewer faults. With FIFO that is not guaranteed. The classic string is 1 2 3 4 1 2 5 1 2 3 4 5 :

The same string under FIFO: 9 faults with three frames, 10 with four. At step 7 the smaller memory holds {5, 1, 2} and the larger {5, 2, 3, 4}: page 1 is in the smaller one only, so the next references hit with three frames and fault with four.

Four frames give 10 faults, one more than three frames . At step 7 the smaller memory holds page 1 and the larger one does not, so the next references to 1 and 2 hit with three frames and fault with four.

Stack algorithms cannot show the anomaly. An algorithm is a stack algorithm if the pages in memory with n frames are always a subset of the pages it would hold with n + 1 frames. LRU qualifies (memory always holds the n most recently used pages) and so does Optimal; FIFO does not, as step 7 shows. On this same string LRU gives 10 faults with three frames and 8 with four.

### Simulating the algorithms

This program counts the faults for each policy and frame count used above; its numbers match the figures.

```
#
include
<algorithm>
#
include
<cstdio>
#
include
<string>
#
include
<vector>
using
namespace
std
;
// Index of the next reference to page after time t; never used again counts as farthest.
int
nextUse
(
const
vector
<
int
>
&
refs
,
int
page
,
int
t
)
{
for
(
int
k
=
t
+
1
;
k
<
(
int
)
refs
.
size
(
)
;
k
++
)
if
(
refs
[
k
]
==
page
)
return
k
;
return
(
int
)
refs
.
size
(
)
;
}
// FIFO keeps frames in load order, LRU in order of last use; the victim is frames[0].
int
countFaults
(
const
vector
<
int
>
&
refs
,
int
n
,
const
string
&
policy
)
{
vector
<
int
>
frames
;
int
faults
=
0
;
for
(
int
t
=
0
;
t
<
(
int
)
refs
.
size
(
)
;
t
++
)
{
int
page
=
refs
[
t
]
;
auto
it
=
find
(
frames
.
begin
(
)
,
frames
.
end
(
)
,
page
)
;
if
(
it
!=
frames
.
end
(
)
)
{
if
(
policy
==
"LRU"
)
{
frames
.
erase
(
it
)
;
frames
.
push_back
(
page
)
;
}
// now most recently used
continue
;
}
faults
++
;
if
(
(
int
)
frames
.
size
(
)
==
n
)
{
int
victim
=
0
;
if
(
policy
==
"OPT"
)
// evict the page whose next use is farthest away
for
(
int
i
=
1
;
i
<
n
;
i
++
)
if
(
nextUse
(
refs
,
frames
[
i
]
,
t
)
>
nextUse
(
refs
,
frames
[
victim
]
,
t
)
)
victim
=
i
;
frames
.
erase
(
frames
.
begin
(
)
+
victim
)
;
}
frames
.
push_back
(
page
)
;
}
return
faults
;
}
string
join
(
const
vector
<
int
>
&
v
)
{
string s
;
for
(
size_t i
=
0
;
i
<
v
.
size
(
)
;
i
++
)
s
+=
(
i
?
" "
:
""
)
+
to_string
(
v
[
i
]
)
;
return
s
;
}
int
main
(
)
{
vector
<
int
>
refs
=
{
2
,
3
,
2
,
1
,
5
,
2
,
4
,
5
,
3
,
2
,
5
,
2
}
;
printf
(
"Reference string: %s\n"
,
join
(
refs
)
.
c_str
(
)
)
;
const
char
*
policies
[
3
]
[
2
]
=
{
{
"FIFO"
,
"FIFO"
}
,
{
"LRU"
,
"LRU"
}
,
{
"OPT"
,
"Optimal"
}
}
;
for
(
auto
&
p
:
policies
)
printf
(
"%s, 3 frames: %d faults\n"
,
p
[
1
]
,
countFaults
(
refs
,
3
,
p
[
0
]
)
)
;
vector
<
int
>
belady
=
{
1
,
2
,
3
,
4
,
1
,
2
,
5
,
1
,
2
,
3
,
4
,
5
}
;
printf
(
"Belady string: %s\n"
,
join
(
belady
)
.
c_str
(
)
)
;
for
(
string policy
:
{
"FIFO"
,
"LRU"
}
)
for
(
int
n
=
3
;
n
<=
4
;
n
++
)
printf
(
"%s, %d frames: %d faults\n"
,
policy
.
c_str
(
)
,
n
,
countFaults
(
belady
,
n
,
policy
)
)
;
return
0
;
}
```

Output

```
Reference string: 2 3 2 1 5 2 4 5 3 2 5 2
FIFO, 3 frames: 9 faults
LRU, 3 frames: 7 faults
Optimal, 3 frames: 6 faults
Belady string: 1 2 3 4 1 2 5 1 2 3 4 5
FIFO, 3 frames: 9 faults
FIFO, 4 frames: 10 faults
LRU, 3 frames: 10 faults
LRU, 4 frames: 8 faults
```

### FIFO vs LRU vs Optimal vs clock

A related choice is global replacement (the victim may belong to any process, which gives better throughput) versus local replacement (only the faulting process's own frames, which keeps one process's behaviour from hurting others). Most general-purpose systems use global replacement.

### Common mistakes

- Forgetting to count the faults that fill the empty frames. Unless a question says otherwise, they count.
- In LRU, evicting by load time instead of last use: a hit must update the page's recency.
- In FIFO, updating the queue on a hit. FIFO ignores hits completely.
- In Optimal, looking backwards instead of forwards, which turns it into LRU.
- Claiming Belady's anomaly happens with LRU. It cannot; only non-stack algorithms such as FIFO show it.
- Thinking the anomaly happens for every string under FIFO. It needs particular strings; usually more frames still help.

### Interview questions

Why is the Optimal algorithm not used in real operating systems? It needs to know which page will be referenced farthest in the future, which the OS cannot know when the fault happens. It is used offline, on recorded reference strings, as a lower bound to compare real algorithms against.

What is Belady's anomaly, and which algorithms suffer from it? It is an increase in page faults when more frames are given. FIFO shows it, for example 9 faults with 3 frames and 10 with 4 on the string 1 2 3 4 1 2 5 1 2 3 4 5. Stack algorithms such as LRU and Optimal never do.

How does the clock algorithm approximate LRU? Every page has a reference bit set by hardware on access. The clock hand sweeps the circular list of frames, clearing bits that are 1 and evicting the first page whose bit is already 0, so pages used since the last sweep survive.

Why prefer evicting a clean page over a dirty one? A dirty page has been modified and must be written back to disk before its frame can be reused, which doubles the I/O for that fault. A clean page can simply be discarded, since an identical copy is already on disk.

What is a stack algorithm? An algorithm for which the pages in memory with n frames are always a subset of those with n + 1 frames. Adding frames can then only turn faults into hits, so the algorithm is immune to Belady's anomaly.

How many page faults does LRU give for the string 7 0 1 2 0 3 0 4 with three frames? Six. The first four references fault while filling and then evicting 7. Page 0 hits, 3 faults and evicts 1, 0 hits, and 4 faults and evicts 2, the least recently used at that point.

Next, read File Systems , or try these on the clock in the Operating Systems (Intermediate) skill test .

### Which page replacement algorithm is the best?

The Optimal algorithm gives the fewest page faults possible, but it needs to know future references, so it cannot be implemented and serves only as a benchmark. LRU comes closest among practical policies, and real systems use cheap approximations of it, such as the clock or second-chance algorithm, because exact LRU needs work on every memory access.

### What is Belady's anomaly?

Belady's anomaly is when giving a process more frames increases its number of page faults. It happens with FIFO: the reference string 1 2 3 4 1 2 5 1 2 3 4 5 causes 9 faults with 3 frames but 10 with 4 frames. LRU and Optimal never show it, because they are stack algorithms.

### Why does LRU not suffer from Belady's anomaly?

LRU is a stack algorithm: the set of pages in memory with n frames is always a subset of the set it would hold with n + 1 frames, because both are simply the n or n + 1 most recently used pages. Adding a frame can therefore only turn faults into hits, never the reverse. FIFO lacks this property.

### How is LRU implemented in practice?

Exact LRU needs either a timestamp written on every memory reference or a stack of pages reordered on every reference, both too slow without special hardware. Operating systems approximate it with the hardware reference bit: the clock or second-chance algorithm, the additional-reference-bits (aging) method, or Linux-style active and inactive lists.

### What is the second chance algorithm?

Second chance is FIFO with a reference bit. When the oldest page is chosen as a victim, its reference bit is checked: if it is 1, the bit is cleared and the page is skipped, getting a second chance; if it is 0, the page is evicted. Implemented with a circular list and a moving pointer, it is called the clock algorithm.


---

## Module 11: Disk Scheduling Algorithms

*Original URL: https://codekairo.com/notes/operating-systems/disk-scheduling*

### Overview

Quick answer

### What is disk scheduling in an operating system?

Disk scheduling is how the operating system orders pending read and write requests for a hard disk to reduce the time spent moving the read-write head. Because seek time dominates a disk access, algorithms such as SSTF, SCAN, C-SCAN, LOOK and C-LOOK reorder the queue to cut total head movement, trading it against fairness and starvation, while FCFS serves requests in arrival order.

- How a disk access is timed
- The example used throughout
- FCFS (First-Come, First-Served)
- SSTF (Shortest Seek Time First)
- SCAN (the elevator algorithm)
- C-SCAN (Circular SCAN)
- LOOK and C-LOOK
- Comparing the algorithms
- Computing the totals
- Choosing an algorithm in practice
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A hard disk serves one request at a time, and the slow part of each request is mechanical: moving the arm to the right track. When many processes have I/O requests pending, the order in which the operating system serves them can change the total time by several times. Disk scheduling is choosing that order. Interviewers give a request queue and a starting head position and ask for the total head movement under each algorithm, so this note works one queue through all six.

### How a disk access is timed

A hard disk has spinning platters , each divided into concentric tracks , and each track into sectors . The tracks at the same position on every platter form a cylinder . One arm moves all the read-write heads together, so requests are described by cylinder number.

Serving one request costs three things:

Access time = seek time + rotational latency + transfer time.

Worked example. A disk spins at 7,200 RPM, has an average seek time of 9 ms and transfers 100 MB/s (100 × 10⁶ bytes per second). One rotation takes 60 ÷ 7,200 s = 8.33 ms, so the average rotational latency is 8.33 ÷ 2 = 4.17 ms. Transferring a 4 KB block takes 4,096 ÷ 100,000,000 s = 0.04 ms. The average access time is 9 + 4.17 + 0.04 ≈ 13.2 ms , almost all of it mechanical. That is why the schedulers below minimize head movement : the total number of cylinders the head travels, used as a stand-in for seek time.

### The example used throughout

- Cylinders numbered 0 to 199 .
- The head is at cylinder 70 , and for the sweeping algorithms it is moving towards higher numbers (towards 199).
- The request queue, in arrival order: 120, 35, 180, 10, 95, 160, 50, 130 .

Sorted, the requests above the head are 95, 120, 130, 160, 180, and below it 50, 35, 10.

Always check a question's conventions: which way the head is moving, whether SCAN goes to the last cylinder, and whether the return jump of C-SCAN and C-LOOK is counted.

### FCFS (First-Come, First-Served)

Serve requests in the order they arrived. It is fair and never starves anyone, but the head swings wildly across the disk.

FCFS serves the queue exactly as it arrived, 120, 35, 180, 10, 95, 160, 50, 130, so the head swings from one side of the disk to the other: 790 cylinders in all, the worst of the six.

Movement: 50 + 85 + 145 + 170 + 85 + 65 + 110 + 80 = 790 cylinders .

### SSTF (Shortest Seek Time First)

Always serve the pending request closest to the current head position, whatever direction it lies in.

The head starts at 70 with 8 requests waiting, the squares on the axis. SSTF ignores arrival order and direction: at every step it serves whichever pending request is nearest the head.

- The head starts at 70 with 8 requests waiting, the squares on the axis. SSTF ignores arrival order and direction: at every step it serves whichever pending request is nearest the head.
- From 70 the nearest pending request is 50, 20 cylinders away (the next nearest, 95, is 25). So the head turns down, away from the requests clustered above it.
- From 50 the nearest pending request is 35, 15 cylinders away (the next nearest, 10, is 40).
- From 35 the nearest pending request is 10, 25 cylinders away (the next nearest, 95, is 60).
- From 10 the nearest pending request is 95, 85 cylinders away (the next nearest, 120, is 110). Nothing is left below, so the head crosses back over 70 and works upwards.
- From 95 the nearest pending request is 120, 25 cylinders away (the next nearest, 130, is 35).
- From 120 the nearest pending request is 130, 10 cylinders away (the next nearest, 160, is 40).
- From 130 the nearest pending request is 160, 30 cylinders away (the next nearest, 180, is 50).
- From 160 the nearest pending request is 180, 20 cylinders away, the last one. Every request is served after 230 cylinders of movement.

Movement: 20 + 15 + 25 + 85 + 25 + 10 + 30 + 20 = 230 cylinders .

SSTF is the SJF of disks: it greatly reduces movement, but a request far from the head can starve while new requests keep arriving near it. It is not optimal either: its greedy choices can make the head zig-zag, and on some queues a planned sweep moves less.

### SCAN (the elevator algorithm)

The head moves in one direction serving every request it passes, goes on to the end of the disk , then reverses and serves the requests on the way back, like a lift that goes to the top floor before coming down.

SCAN serves 95, 120, 130, 160, 180 on the way up, carries on to cylinder 199 although nothing waits there, then reverses and serves 50, 35, 10: 318 cylinders.

Movement: up from 70 to 199 is 129, then down from 199 to 10 is 189, so 318 cylinders .

SCAN cannot starve a request: every cylinder is passed within two sweeps. Its weakness is uneven waiting. Just after the head turns, the requests right behind it were served moments ago, while those at the far end have waited longest; cylinders near the middle are passed twice as often as those at the edges.

### C-SCAN (Circular SCAN)

Serve requests in one direction only . On reaching the end of the disk, the head returns to cylinder 0 without serving anything and sweeps upward again, treating the cylinders as a circle.

C-SCAN sweeps up to 199, returns to 0 without serving anything (dashed), and serves 10, 35, 50 on the next upward sweep: 378 cylinders counting the return, 179 without it.

Movement: 70 to 199 is 129, the return from 199 to 0 is 199, and 0 to 50 is 50, so 378 cylinders counting the return, or 179 if the return jump is not counted. Textbooks differ on this; say which you use.

C-SCAN moves more than SCAN but gives more uniform waiting times , because every cylinder is visited once per cycle in the same direction.

### LOOK and C-LOOK

LOOK and C-LOOK are SCAN and C-SCAN with one change: the head goes only as far as the last request in its direction, never to the physical end of the disk.

LOOK sweeps up to 180, the highest request, and reverses there instead of going on to 199, then serves 50, 35, 10 on the way down: 280 cylinders.

- LOOK sweeps up to 180, the highest request, and reverses there instead of going on to 199, then serves 50, 35, 10 on the way down: 280 cylinders.
- C-LOOK serves only on the way up. From 180 it jumps straight to 10, the lowest pending request (dashed, serving nothing), and sweeps up again: 320 cylinders counting the jump, 150 without it.

LOOK goes up to the highest request, then reverses. Movement: 70 to 180 is 110, then 180 down to 10 is 170, so 280 cylinders .

C-LOOK goes up to the highest request, then jumps to the lowest pending request and sweeps up again. Movement: 70 to 180 is 110, the jump from 180 to 10 is 170, and 10 to 50 is 40, so 320 cylinders counting the jump, or 150 without it.

### Comparing the algorithms

SSTF moves least on this queue, LOOK beats SCAN and C-LOOK beats C-SCAN because neither travels to an edge with no request there, and FCFS is worst by a wide margin. The ranking depends on the queue; the pattern of LOOK ≤ SCAN and C-LOOK ≤ C-SCAN always holds.

### Computing the totals

This program builds each algorithm's service order from the same queue and adds up the head movement, counting the return jumps of C-SCAN and C-LOOK.

```
#
include
<algorithm>
#
include
<cstdio>
#
include
<cstdlib>
#
include
<string>
#
include
<vector>
using
namespace
std
;
const
int
HEAD
=
70
,
LAST
=
199
;
// head position, last cylinder; the head is moving up
const
vector
<
int
>
QUEUE
=
{
120
,
35
,
180
,
10
,
95
,
160
,
50
,
130
}
;
vector
<
int
>
sstf
(
)
{
vector
<
int
>
left
=
QUEUE
,
path
=
{
HEAD
}
;
int
at
=
HEAD
;
while
(
!
left
.
empty
(
)
)
{
size_t best
=
0
;
// closest request; a tie goes to the lower cylinder
for
(
size_t i
=
1
;
i
<
left
.
size
(
)
;
i
++
)
{
int
d
=
abs
(
left
[
i
]
-
at
)
,
b
=
abs
(
left
[
best
]
-
at
)
;
if
(
d
<
b
||
(
d
==
b
&&
left
[
i
]
<
left
[
best
]
)
)
best
=
i
;
}
at
=
left
[
best
]
;
left
.
erase
(
left
.
begin
(
)
+
best
)
;
path
.
push_back
(
at
)
;
}
return
path
;
}
void
print
(
const
string
&
name
,
const
vector
<
int
>
&
path
)
{
int
total
=
0
;
string s
;
for
(
size_t i
=
0
;
i
<
path
.
size
(
)
;
i
++
)
{
if
(
i
>
0
)
total
+=
abs
(
path
[
i
]
-
path
[
i
-
1
]
)
;
s
+=
(
i
?
" "
:
""
)
+
to_string
(
path
[
i
]
)
;
}
printf
(
"%s: %s | total %d\n"
,
name
.
c_str
(
)
,
s
.
c_str
(
)
,
total
)
;
}
vector
<
int
>
concat
(
initializer_list
<
vector
<
int
>>
parts
)
{
vector
<
int
>
out
;
for
(
const
auto
&
p
:
parts
)
out
.
insert
(
out
.
end
(
)
,
p
.
begin
(
)
,
p
.
end
(
)
)
;
return
out
;
}
int
main
(
)
{
vector
<
int
>
up
,
down
;
for
(
int
c
:
QUEUE
)
(
c
>=
HEAD
?
up
:
down
)
.
push_back
(
c
)
;
sort
(
up
.
begin
(
)
,
up
.
end
(
)
)
;
// served on the way up
sort
(
down
.
rbegin
(
)
,
down
.
rend
(
)
)
;
// below the head, nearest first
vector
<
int
>
lowFirst
(
down
.
rbegin
(
)
,
down
.
rend
(
)
)
;
// below the head, lowest first
print
(
"FCFS"
,
concat
(
{
{
HEAD
}
,
QUEUE
}
)
)
;
print
(
"SSTF"
,
sstf
(
)
)
;
print
(
"SCAN"
,
concat
(
{
{
HEAD
}
,
up
,
{
LAST
}
,
down
}
)
)
;
print
(
"C-SCAN"
,
concat
(
{
{
HEAD
}
,
up
,
{
LAST
,
0
}
,
lowFirst
}
)
)
;
print
(
"LOOK"
,
concat
(
{
{
HEAD
}
,
up
,
down
}
)
)
;
print
(
"C-LOOK"
,
concat
(
{
{
HEAD
}
,
up
,
lowFirst
}
)
)
;
return
0
;
}
```

Output

```
FCFS: 70 120 35 180 10 95 160 50 130 | total 790
SSTF: 70 50 35 10 95 120 130 160 180 | total 230
SCAN: 70 95 120 130 160 180 199 50 35 10 | total 318
C-SCAN: 70 95 120 130 160 180 199 0 10 35 50 | total 378
LOOK: 70 95 120 130 160 180 50 35 10 | total 280
C-LOOK: 70 95 120 130 160 180 10 35 50 | total 320
```

### Choosing an algorithm in practice

For a lightly loaded disk the queue is rarely longer than one or two requests, and every algorithm behaves like FCFS. Under heavy load, SCAN-family algorithms avoid starvation and keep throughput high; textbooks traditionally name SSTF or LOOK as a reasonable default, with C-LOOK where uniform waiting matters. Real schedulers also weigh deadlines, so a read a process is blocked on is not held back too long, and the disk's own controller reorders requests internally.

Solid-state drives have no arm and no rotation, so the time of a request barely depends on its address and head-movement scheduling buys nothing. Linux, for example, offers several block-layer schedulers, including mq-deadline , bfq , kyber and none , and fast NVMe SSDs commonly run with none , simply passing requests through in order.

### Common mistakes

- Running SCAN in the wrong direction. The direction is part of the question; going down first from 70 gives a different total.
- Sending LOOK to cylinder 199 or 0. LOOK turns at the last request; only SCAN and C-SCAN touch the ends.
- Counting or not counting the C-SCAN and C-LOOK return jump without saying so. State the convention every time.
- Serving requests on the return sweep of C-SCAN. The return is a single jump with no service.
- Breaking an SSTF tie arbitrarily and getting a different answer from the key. When two requests are equally close, follow the question's rule (often the lower cylinder, or the current direction).
- Assuming SSTF is optimal. It is greedy, and on some queues a planned sweep moves less.

### Interview questions

What is the difference between seek time and rotational latency? Seek time is the time to move the arm to the right cylinder and depends on the distance moved. Rotational latency is the wait for the sector to spin under the head, on average half a rotation, about 4.17 ms at 7,200 RPM.

Why is SCAN called the elevator algorithm? It works like a lift: the head travels in one direction serving every request on the way, goes to the end, then reverses and serves the requests in the other direction.

Why does C-SCAN give more uniform waiting time than SCAN? In SCAN, after the head reverses, it first serves the cylinders it has just passed, while requests at the far end have been waiting longest. C-SCAN always sweeps the same way and returns to the start, so every cylinder is visited once per cycle at regular intervals.

Can SSTF cause starvation? How do SCAN-type algorithms avoid it? Yes. A request far from the head can be skipped forever if closer requests keep arriving. SCAN-type algorithms sweep the full range in order, so every pending request is reached within one or two sweeps.

Which algorithm gives the minimum head movement? On a particular queue it is often SSTF, but no simple rule always gives the minimum, and SSTF's greedy choices can cost more on some queues. LOOK never moves more than SCAN, and C-LOOK never more than C-SCAN.

Does disk scheduling matter for SSDs? Much less. An SSD has no moving head, so access time hardly depends on location, and reordering by address does not help. Schedulers for SSDs focus on fairness and latency between processes, or simply pass requests through.

Next, read Inter-Process Communication , or test yourself with the Operating Systems (Intermediate) skill test .

### Which disk scheduling algorithm is best?

There is no single best one. SSTF usually gives the least head movement but can starve requests far from the head. SCAN and LOOK give good throughput with no starvation, and C-SCAN and C-LOOK give the most uniform waiting times. LOOK or C-LOOK is a common choice for a busy hard disk; for an SSD, which has no head, simple FCFS ordering is enough.

### What is the difference between SCAN and LOOK?

SCAN moves the head all the way to the last cylinder in its direction of travel before reversing, even if no request lies there. LOOK reverses as soon as it has served the last request in that direction. LOOK therefore never travels further than SCAN and usually less.

### What is the difference between SCAN and C-SCAN?

SCAN serves requests in both directions, sweeping up and then back down like a lift. C-SCAN serves requests in one direction only: after reaching the end it jumps straight back to the other end without serving anything and starts again. C-SCAN gives more uniform waiting times, because cylinders in the middle are not visited twice as often as the edges.

### What are seek time and rotational latency?

Seek time is the time for the disk arm to move the head to the cylinder holding the data. Rotational latency is the time for the wanted sector to rotate under the head once it is there, on average half a rotation. Together with the transfer time they make up the access time of a hard disk request.

### Why does SSTF cause starvation?

SSTF always serves the pending request closest to the current head position. If new requests keep arriving near the head, a request at a far cylinder is never the closest, so it can wait indefinitely. SCAN-family algorithms avoid this because the head sweeps across the whole disk in order.


---

## Module 12: File Systems

*Original URL: https://codekairo.com/notes/operating-systems/file-systems*

### Overview

Quick answer

### What is a file system in an operating system?

A file system is the part of the operating system that organizes data on a storage device into named files and directories. It records each file's attributes, decides which disk blocks hold its data through an allocation method such as contiguous, linked or indexed allocation, tracks free space, and enforces permissions. Examples are ext4 on Linux, NTFS on Windows, APFS on macOS and FAT32 on USB drives.

- Files and their attributes
- Access methods
- Directory structures
- Allocation methods
- Inodes in Unix file systems
- Free-space management
- FAT (File Allocation Table)
- Consistency and journaling
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A disk is just a long array of numbered blocks. A file system is what turns those blocks into named files in directories, with sizes, owners and permissions, and keeps that structure consistent as files grow, shrink and disappear. It has to answer three questions for every file: what is it called and who may use it, which blocks hold its data, and which blocks are still free.

### Files and their attributes

A file is a named collection of related information stored on secondary storage; it is the smallest unit a user can write to storage. The OS keeps these attributes for every file:

The basic file operations are create, open, read, write, reposition (seek), close, delete and truncate. Because searching the directory on every access would be slow, open() looks the file up once and returns a file descriptor , an index into a per-process open-file table . That entry holds the current file position and points into a system-wide table that holds the file's attributes and a count of how many processes have it open.

### Access methods

Sequential access is easy to simulate on a direct-access file, by keeping a current position; the reverse is slow.

### Directory structures

A directory maps file names to the files themselves, either holding their attributes or pointing to them.

Tree-structured directories give path names : absolute paths start at the root ( /home/asha/notes.txt ), relative paths start at the current working directory ( notes.txt ). Unix file systems are acyclic graphs in practice, thanks to two kinds of link:

- A hard link is a second directory entry naming the same inode. The inode keeps a link count , and the data is freed only when it falls to zero. Hard links cannot cross file systems, and directories cannot be hard-linked apart from the . and .. entries the system creates, which keeps the graph free of cycles.
- A symbolic (soft) link is a tiny file that contains a path. It can point anywhere, even across file systems or to a directory, but it dangles if the target is deleted or moved.

notes.txt and copy.txt are two directory entries for the same inode, so its link count is 2 and neither name is the original. short has an inode of its own whose data is just the name notes.txt, looked up each time it is opened.

- notes.txt and copy.txt are two directory entries for the same inode, so its link count is 2 and neither name is the original. short has an inode of its own whose data is just the name notes.txt, looked up each time it is opened.
- rm notes.txt removes one directory entry: the count drops to 1 and copy.txt still reaches the data, freed only when the count reaches 0. short still holds notes.txt, a name that no longer exists, so it dangles.

### Allocation methods

How a file's data is placed on disk decides how fast it can be read and how well space is used. Assume the disk has numbered blocks and nothing is cached except the directory entry. Here is one five-block file placed each way, and what it takes to reach its logical block 3:

Contiguous: the file is blocks 14 to 18 and the directory keeps the start and length. Logical block 3 is at 14 + 3 = 17, found by arithmetic: one read.

- Contiguous: the file is blocks 14 to 18 and the directory keeps the start and length. Logical block 3 is at 14 + 3 = 17, found by arithmetic: one read.
- Linked: the blocks are scattered and each holds the number of the next. Reaching logical block 3 means reading 9, 16, 1 for their pointers first: 4 reads, and block 50 would take 51.
- Indexed: block 4 lists the file's blocks in order. Read it, take entry 3, which is block 10, and read that: two reads for any block, at the cost of a whole block for the index.

### Contiguous allocation

Each file occupies a run of consecutive blocks; the directory stores the start block and length , so logical block i is simply at start + i.

- Sequential and random access are both fast: one computation, one read, minimal head movement.
- External fragmentation builds up as files are created and deleted, exactly as with contiguous memory allocation.
- Files are hard to grow: the next blocks may be taken, so the file must be moved or its size declared in advance.

Extents , used by ext4 and NTFS, keep the benefit while allowing growth: a file is a short list of contiguous runs, each recorded as (start, length).

### Linked allocation

Each file is a linked list of blocks scattered anywhere; the directory holds the first and last block, and each block holds a pointer to the next.

- No external fragmentation, and files grow freely.
- Random access is slow : reaching logical block i means reading the i blocks before it to follow the pointers.
- Each block loses a few bytes to the pointer.

### Indexed allocation

All of a file's block addresses are gathered into one index block , the directory points to it, and entry i holds the address of logical block i.

- Fast random access and no external fragmentation.
- The index block costs space even for a tiny file, and a large file needs more than one index block: a linked list of index blocks, a multilevel index , or the combined scheme of the Unix inode below.

Reads needed to fetch logical block 50 of a file:

### Inodes in Unix file systems

Unix file systems such as ext2 and ext3 use a combined indexed scheme. Each file has an inode holding its type, permissions, owner, size, timestamps, link count and 15 block pointers : 12 direct pointers to data blocks, then a single indirect pointer to a block full of data-block pointers, a double indirect one level deeper and a triple indirect one level deeper again. Small files are reached with no extra reads, while the indirect levels let files grow very large.

The inode holds the file's attributes (no name) and 15 pointers. Twelve point straight at data, 48 KB; the indirect ones point at blocks of 1,024 pointers, one, two and three levels deep, reaching 4 MB, 4 GB and 4 TB.

- The inode holds the file's attributes (no name) and 15 pointers. Twelve point straight at data, 48 KB; the indirect ones point at blocks of 1,024 pointers, one, two and three levels deep, reaching 4 MB, 4 GB and 4 TB.
- Byte 60,000 is in logical block 14. Blocks 12 to 1,035 go through the single indirect block, at entry 14 − 12 = 2: read that block, then the data. Two reads.
- Byte 10,485,760 (10 MB) is in block 2,560, past 1,035, so in the double indirect range at position 1524: entry 1 of the first index block, entry 500 of the second, then the data. Three reads.

Worked example: maximum file size. Blocks are 4 KB and a block pointer is 4 bytes, so one block holds 4096 ÷ 4 = 1,024 pointers .

That is the textbook limit of the pointer structure. Real file systems add other limits, such as the width of the size field, and ext4 replaces the indirect blocks with extents by default.

Worked example: reads to reach a byte , with the inode already in memory. Logical blocks 0 to 11 are direct, 12 to 1,035 go through the single indirect block, and 1,036 to 1,049,611 through the double indirect block. Byte 60,000 is in block 60000 ÷ 4096 = 14, single indirect: 2 reads . Byte 10,485,760 (10 MB) is in block 2,560, double indirect: 3 reads .

### Free-space management

The file system must know which blocks are free.

Bitmap example. If 1 means free, the bitmap 0 0 1 1 1 0 0 1 for blocks 0 to 7 says blocks 2, 3, 4 and 7 are free; the free run 2 to 4 is visible at a glance. For a 1 TB disk with 4 KB blocks there are 2⁴⁰ ÷ 2¹² = 2²⁸ blocks, so the bitmap is 2²⁸ bits = 32 MB , which is why large file systems split it into groups and load only parts.

### FAT (File Allocation Table)

FAT is linked allocation with the pointers moved out of the data blocks into one table at the start of the volume. The table has one entry per cluster (a group of sectors): an entry holds the number of the file's next cluster, an end-of-file mark, or 0 for a free cluster. The directory entry stores a file's first cluster.

The directory gives the first cluster, 4; its FAT entry gives the next, and so on until an end mark: 4, 7, 2, 10. The whole walk happens in the cached table, so only the wanted cluster is read from disk, and free entries double as the free-space list.

Caching the whole table turns linked allocation's worst problem, slow random access, into a walk through RAM, and the FAT doubles as the free-space list. FAT32 uses 28-bit cluster numbers and limits a single file to 4 GB minus 1 byte, which is why larger drives use exFAT or NTFS, but its simplicity keeps it on memory cards and USB drives.

### Consistency and journaling

A crash in the middle of an update, say after a block is allocated but before the inode points to it, leaves the structures inconsistent. Older systems ran a checker such as fsck over the whole disk at boot. Journaling file systems, including ext4, NTFS and XFS, first write each update as a transaction to a log, the journal, and only then to its real place. After a crash only the journal needs replaying, which takes seconds instead of a full scan. Most journal only metadata by default; ext4's default ordered mode also writes data blocks before the metadata that points to them is committed.

### Common mistakes

- Saying the inode stores the file name. The name is in the directory entry.
- Treating linked allocation and FAT as unrelated. FAT is linked allocation with the links kept in a table.
- Forgetting that contiguous allocation suffers external fragmentation, not internal.
- Saying a hard link and a symbolic link behave the same when the original is deleted. The hard link still works; the symbolic link dangles.
- Computing pointers per block as block size in bits divided by pointer size in bytes. Use bytes for both: 4096 ÷ 4 = 1,024.
- Thinking a journal makes every write safe. Journaling protects the file system's structure; whether file data is protected depends on the mode.

### Interview questions

Which allocation method is best for random access, and why? Contiguous allocation: the address of any logical block is start + i, so one read reaches it. Indexed allocation is close behind, needing one extra read for the index block, while linked allocation must follow every pointer before the wanted block.

How large can a file be with 12 direct, one single, one double and one triple indirect pointer, 4 KB blocks and 4-byte pointers? Each block holds 1,024 pointers, so the file can have 12 + 1,024 + 1,024² + 1,024³ blocks of 4 KB: 48 KB + 4 MB + 4 GB + 4 TB, just over 4 TB.

What happens to a file's data when you delete one of its hard links? Only that directory entry is removed and the inode's link count drops by one. The data is freed when the count reaches zero and no process still has the file open.

Why does FAT allow faster random access than plain linked allocation? In plain linked allocation each next-pointer is inside a data block, so following the chain means reading those blocks from disk. FAT keeps all the pointers in one table that can be cached, so the chain is followed in memory and only the wanted block is read.

What is the difference between a file descriptor and an inode? An inode describes a file on disk and exists whether or not anyone is using it. A file descriptor is a small integer a process gets from open() , indexing its open-file table, which records the current position and refers to the in-memory copy of the inode.

Why do file systems use bitmaps for free space? A bitmap is compact enough to keep in memory and makes it fast to find a free block, or a run of free blocks near a file, by scanning words for set bits. Allocating contiguous runs keeps files less fragmented and reads faster.

Next, read Disk Scheduling Algorithms , or test yourself with the Operating Systems (Intermediate) skill test .

### What are the file allocation methods in an operating system?

Contiguous allocation stores a file in consecutive blocks, which is fast for any access but causes external fragmentation and makes files hard to grow. Linked allocation chains blocks with pointers, which removes fragmentation but makes random access slow. Indexed allocation keeps all of a file's block addresses in an index block, giving fast random access at the cost of the index's space.

### What is an inode?

An inode is the Unix data structure that describes one file: its type, permissions, owner, size, timestamps, link count and the addresses of its data blocks, through direct and indirect pointers. It does not contain the file's name; a directory maps names to inode numbers, which is why one file can have several names through hard links.

### What is the difference between a hard link and a soft link?

A hard link is another directory entry pointing to the same inode, so both names are equally the file, and the data is freed only when the last link is removed. A soft or symbolic link is a small file containing a path to the target; it can cross file systems and point to directories, but it breaks if the target is deleted.

### What is a FAT file system?

FAT, the File Allocation Table, is a linked-allocation file system that keeps all the next-block pointers in one table at the start of the volume, with one entry per cluster. A directory entry gives a file's first cluster, and each table entry gives the next cluster or an end-of-file mark. FAT32 is still common on USB drives and memory cards.

### How does an operating system keep track of free disk space?

With a free-space list in one of several forms: a bitmap with one bit per block, a linked list of free blocks, grouping where one free block stores the addresses of many others, or counting, which records runs as a start block and a length. Bitmaps are the most common because finding a run of free blocks is fast.


---

