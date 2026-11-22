# Object-Oriented Programming (OOPS)

> **Source**: [CodeKairo CS Notes](https://codekairo.com/notes/oop)  
> **Overview**: Comprehensive Object-Oriented Programming and Design guide covering Classes, Objects, Encapsulation, Abstraction, Inheritance, Polymorphism, SOLID principles, GoF design patterns, Composition, and Exception Handling.

---

## Table of Modules

1. [Introduction to Object-Oriented Programming](#module-1-introduction-to-object-oriented-programming)
2. [Classes and Objects](#module-2-classes-and-objects)
3. [Encapsulation](#module-3-encapsulation)
4. [Abstraction: Abstract Classes and Interfaces](#module-4-abstraction-abstract-classes-and-interfaces)
5. [Inheritance](#module-5-inheritance)
6. [Polymorphism](#module-6-polymorphism)
7. [SOLID Principles](#module-7-solid-principles)
8. [Design Patterns for Interviews](#module-8-design-patterns-for-interviews)
9. [Association, Aggregation and Composition](#module-9-association,-aggregation-and-composition)
10. [Object Equality, Hashing and Copying](#module-10-object-equality,-hashing-and-copying)
11. [Exception Handling in OOP](#module-11-exception-handling-in-oop)

---

## Module 1: Introduction to Object-Oriented Programming

*Original URL: https://codekairo.com/notes/oop/introduction-to-oop*

### Overview

Quick answer

### What is object-oriented programming (OOP)?

Object-oriented programming is a way of organising a program around objects, each bundling data (its state) with the functions that work on that data (its behaviour). Classes describe what kind of object to make, and the four pillars — encapsulation, abstraction, inheritance and polymorphism — describe how objects hide details, share code and stand in for one another.

- What object-oriented programming means
- Procedural vs object-oriented programming
- Classes and objects
- The four pillars of OOP
- The four pillars in one program
- Benefits and costs of OOP
- OOP in C++ vs Java vs Python
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Object-oriented programming (OOP) is a way of structuring a program as a set of objects that each hold some data and the operations allowed on that data. Instead of passing a bank balance to whichever function needs it, you build an Account object that owns its balance and offers deposit and withdraw ; nothing else touches the number directly. OOP exists because large programs grow faster than anyone can hold in their head, and grouping data with the code that guards it keeps each change in one place. C++, Java, Python, C# and JavaScript all support it, so an interviewer can ask you to explain it in whichever language you list on your resume.

### What object-oriented programming means

The vocabulary is small, and every later note builds on it:

- An object has three things: state (the current values of its fields, also called attributes or data members), behaviour (its methods — functions that belong to it) and identity (it is itself, even if another object holds identical values).
- A class is the blueprint for objects: it declares which fields each object has and defines the methods. Making an object from a class is called instantiation ; the object is an instance of the class.
- Objects work together by calling each other's methods. Older texts call this message passing : you ask an object to do something, and the object decides how.

A running OOP program is therefore a group of objects, each responsible for its own data, collaborating through method calls. The design question shifts from "what steps does the program take?" to "what things exist, what does each one know, and what can each one do?"

### Procedural vs object-oriented programming

Procedural programming — the style of C or Pascal — organises a program as functions that act on data passed to them. OOP moves the functions next to the data. Neither is "better" in general; they make different changes cheap.

Left: the balances sit in plain records that every function is handed, so nothing stops some other line from writing a negative balance. Right: each object holds its own balance (500 and 1000), and only its own methods can change it.

The last two rows are the honest trade-off, and they are easiest to see as a grid of types against operations:

In OOP every row of this grid is a class. Adding Circle is one new class written in one place; adding perimeter() means opening both existing classes to add a method.

- In OOP every row of this grid is a class. Adding Circle is one new class written in one place; adding perimeter() means opening both existing classes to add a method.
- Procedural code groups the same grid by column: each operation is one function that switches on the kind of shape. Adding perimeter() is one new function; adding Circle means a new case in both existing functions.

You can also write object-style code in a procedural language — the Linux kernel's struct file_operations is a table of function pointers that each file system fills in, which is hand-made polymorphism in C — but the language gives you no help enforcing it.

### Classes and objects

Here is one class and two objects, run statement by statement:

The class is only a definition. The constructor call makes the first object, with its own owner and balance: asha starts with Rs 500.

- The class is only a definition. The constructor call makes the first object, with its own owner and balance: asha starts with Rs 500.
- A second object from the same class gets its own copy of every field: ravi's balance is 1000, and the two objects share nothing but their methods.
- deposit runs on asha alone: her balance becomes 750, and ravi's 1000 does not move. The method found the right balance through the object it was called on.
- 1500 is more than ravi's 1000, so withdraw refuses and returns false. The balance cannot go negative because no code outside the class can write it.
- A withdrawal the balance can cover goes through: 1000 − 300 = 700.
- Each object reports its own state: Asha has Rs 750, Ravi has Rs 700. One class, two objects, each with its own data and the same guarded behaviour.

```
#
include
<iostream>
#
include
<string>
using
namespace
std
;
class
Account
{
string owner
;
int
balance
;
// private: only Account's own methods can touch it
public
:
Account
(
string owner
,
int
opening
)
:
owner
(
owner
)
,
balance
(
opening
)
{
}
void
deposit
(
int
amount
)
{
balance
+=
amount
;
}
bool
withdraw
(
int
amount
)
{
if
(
amount
>
balance
)
return
false
;
// the object guards its own rule
balance
-=
amount
;
return
true
;
}
void
show
(
)
const
{
cout
<<
owner
<<
" has Rs "
<<
balance
<<
"\n"
;
}
}
;
int
main
(
)
{
Account
asha
(
"Asha"
,
500
)
;
// two objects of one class,
Account
ravi
(
"Ravi"
,
1000
)
;
// each with its own state
asha
.
deposit
(
250
)
;
if
(
!
ravi
.
withdraw
(
1500
)
)
cout
<<
"Ravi: withdrawal refused\n"
;
ravi
.
withdraw
(
300
)
;
asha
.
show
(
)
;
ravi
.
show
(
)
;
return
0
;
}
```

Output

```
Ravi: withdrawal refused
Asha has Rs 750
Ravi has Rs 700
```

Notice what the Python version does differently: there is no private keyword, only the underscore convention. Python trusts the caller; C++ and Java make the compiler refuse. The next note, Classes and Objects , covers constructors, this / self , static members and where objects live in memory.

### The four pillars of OOP

Almost every interview starts here. Learn one sentence of definition and one example for each.

### Encapsulation

Encapsulation is bundling an object's data with the methods that operate on it and restricting direct access to that data, so the object can keep its own rules (its invariants ) true. The Account above is encapsulated: the balance can only change through deposit and withdraw , so it can never go negative. Access modifiers ( private , protected , public ) are the language tool for it. Full detail: Encapsulation .

### Abstraction

Abstraction is showing what an object does and hiding how it does it. A caller sees withdraw(amount) ; it does not see the database row, the audit log or the fraud check behind it. Abstract classes and interfaces are how you write an abstraction down as a type: "anything that can pay(amount) ", with the details left to each implementation. Full detail: Abstraction .

### Inheritance

Inheritance lets a class (the subclass , child or derived class) reuse and extend another class (the superclass , parent or base class). It models an is-a relationship: a SavingsAccount is an Account , so it gets deposit and withdraw for free and adds addInterest . It is powerful and easily overused; often you should build objects out of other objects instead. Full detail: Inheritance .

### Polymorphism

Polymorphism ("many forms") means one interface, many implementations: code written against Shape works for every kind of shape, and each shape answers area() in its own way. Compile-time polymorphism is overloading (same method name, different parameters); run-time polymorphism is overriding, where the object's actual class picks the method while the program runs. Full detail: Polymorphism .

### The four pillars in one program

One small program shows all four at once. The figure points at each pillar in its class diagram; the code follows.

Abstraction: Shape says what every shape can do, name() and area(), and says nothing about how. It cannot be instantiated; callers are written against it.

- Abstraction: Shape says what every shape can do, name() and area(), and says nothing about how. It cannot be instantiated; callers are written against it.
- Encapsulation: each concrete class keeps its own dimensions private. Nothing outside Rectangle can read or change w and h, so a rectangle's area depends only on its own constructor's values.
- Inheritance: Rectangle and Triangle are kinds of Shape (the hollow triangles point at the parent), so either one can be used wherever a Shape is expected.
- Polymorphism: the loop calls s.area() without knowing which shape it holds, and each object runs its own class's version — 20 for the rectangle, 12 for the triangle, 32 in total.

```
#
include
<iostream>
#
include
<memory>
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
class
Shape
{
// abstraction: what every shape can do
public
:
virtual
~
Shape
(
)
=
default
;
virtual
string
name
(
)
const
=
0
;
virtual
int
area
(
)
const
=
0
;
}
;
class
Rectangle
:
public
Shape
{
// inheritance
int
w
,
h
;
// encapsulation: private dimensions
public
:
Rectangle
(
int
w
,
int
h
)
:
w
(
w
)
,
h
(
h
)
{
}
string
name
(
)
const
override
{
return
"Rectangle"
;
}
int
area
(
)
const
override
{
return
w
*
h
;
}
}
;
class
Triangle
:
public
Shape
{
int
base
,
height
;
public
:
Triangle
(
int
b
,
int
h
)
:
base
(
b
)
,
height
(
h
)
{
}
string
name
(
)
const
override
{
return
"Triangle"
;
}
int
area
(
)
const
override
{
return
base
*
height
/
2
;
}
}
;
int
main
(
)
{
vector
<
unique_ptr
<
Shape
>>
shapes
;
shapes
.
push_back
(
make_unique
<
Rectangle
>
(
4
,
5
)
)
;
shapes
.
push_back
(
make_unique
<
Triangle
>
(
6
,
4
)
)
;
int
total
=
0
;
for
(
const
auto
&
s
:
shapes
)
{
// polymorphism: each shape answers area() its own way
cout
<<
s
->
name
(
)
<<
": "
<<
s
->
area
(
)
<<
"\n"
;
total
+=
s
->
area
(
)
;
}
cout
<<
"Total area: "
<<
total
<<
"\n"
;
return
0
;
}
```

Output

```
Rectangle: 20
Triangle: 12
Total area: 32
```

### Benefits and costs of OOP

What OOP buys you:

- Locality of change. The rules for an account live in Account . Fixing a bug or changing a rule touches one class.
- Protected invariants. Encapsulation means no stray function can set a balance to −500.
- Reuse. Composition and inheritance let new classes build on tested ones.
- Extensibility. With polymorphism, a new Circle class works with every function that already takes a Shape , with no edits to those functions.
- A shared vocabulary. Classes named after the domain ( Order , Invoice , Shipment ) make code easier to discuss with people who are not programmers.

What it costs:

- Indirection. Following a call through an interface to the right implementation takes longer than reading one function.
- Up-front design. Bad class boundaries are expensive to move later; deep inheritance trees are the classic example.
- Overhead in small programs. A 40-line script rarely needs a class hierarchy.
- Performance in tight loops. Virtual calls and scattered heap objects can be slower than plain arrays processed by one function; game engines and numeric code often use data-oriented designs for this reason.

### OOP in C++ vs Java vs Python

All three support the same ideas with different defaults. This table is worth memorising because interviewers like the "how does language X do it" follow-up.

Duck typing means Python cares whether an object has the method you call, not which class it belongs to: "if it walks like a duck and quacks like a duck, it is a duck".

### Common mistakes

- Saying a class and an object are the same thing — a class is the definition, an object is an instance made at run time.
- Calling Java "100% object-oriented" — int , double and the other primitives are not objects, and static methods run without one.
- Thinking getters and setters for every field is encapsulation; exposing every field through methods hides nothing.
- Mixing up abstraction (hiding how ) with encapsulation (bundling and protecting data ).
- Reaching for inheritance whenever two classes share code; composition is usually the safer default.
- Assuming every method in C++ is overridable at run time — without virtual it is not.

### Interview questions

What is the difference between procedural and object-oriented programming? Procedural code is organised as functions that operate on data passed to them; object-oriented code bundles the data and the functions into objects. OOP adds access control, inheritance and polymorphism, which make adding new types of data cheap. Procedural code makes adding new operations cheap, since one new function can handle every kind of data.

Explain the four pillars of OOP with one example. Take a payment system. Encapsulation: a Wallet keeps its balance private and changes it only through pay . Abstraction: callers depend on a PaymentMethod with a pay(amount) method. Inheritance: UpiPayment and CardPayment extend PaymentMethod . Polymorphism: checkout(method) calls method.pay(amount) and the right version runs for whichever object was passed.

Does a class occupy memory? The class's code, its static fields and its metadata (such as a vtable in C++ or the class object in Java and Python) exist once. Memory for instance fields is allocated only when an object is created, once per object. So declaring a class does not allocate any per-object storage.

What is the difference between a class and a struct in C++? Only the defaults: members of a struct are public by default and members of a class are private, and a struct inherits publicly by default while a class inherits privately. Both can have constructors, methods, virtual functions and inheritance. By convention, struct is used for plain data and class for types with invariants.

Why is Java not considered a purely object-oriented language? It has eight primitive types ( int , long , double , boolean and so on) that are not objects, and static methods and fields can be used without any object at all. Wrapper classes such as Integer and autoboxing paper over the first point but do not remove it.

Can you write object-oriented code in C? Yes, by hand. A struct holds the state, function pointers in the struct give each "class" its own behaviour, and an opaque pointer declared in a header hides the fields from callers. The language does not check any of it — there is no inheritance, no access control and no automatic dispatch.

What is message passing in OOP? It is the idea that objects interact by asking each other to do things — calling a method on an object — and the receiving object decides how to respond. With run-time polymorphism, the same call can run different code depending on the receiver's actual class.

When would you avoid OOP? For short scripts, one-off data transformations and pipelines that are naturally a chain of functions, classes add ceremony without benefit. Performance-critical code that processes millions of similar items often stores them in plain arrays instead of separate objects, for better cache use.

Next, read Classes and Objects , then check yourself with the OOP Basic skill test .

### What is an object in OOP?

An object is one thing your program works with, made from a class. It has state (the values of its fields), behaviour (the methods you can call on it) and identity (it is a distinct object even if another one holds exactly the same values).

### What is the difference between a class and an object?

A class is a definition: the fields every object will have and the methods that work on them. An object is one instance of that class created at run time, with its own values for those fields. Student is a class; the student with roll number 42 is an object.

### Is C++ a pure object-oriented language?

No. C++ is multi-paradigm: you can write free functions and global variables, and values such as int are not objects with methods. Java is closer but still has primitive types and static methods. Smalltalk is the usual example of a pure object-oriented language, where every value is an object.

### Is Python an object-oriented language?

Yes. Every value in Python — integers, strings, functions, even classes themselves — is an object with a type. Python also lets you write plain functions and top-level scripts, so it is multi-paradigm: you use classes where they help and skip them where they do not.

### What are the advantages of OOP?

Code is grouped around the things it models, so a change usually stays inside one class. Encapsulation protects each object's rules, inheritance and composition reuse code, and polymorphism lets a new type plug into existing code without editing it. The price is more indirection and more design up front.

### Which was the first object-oriented programming language?

Simula 67, designed by Ole-Johan Dahl and Kristen Nygaard in Norway, introduced classes, objects, inheritance and virtual procedures. Smalltalk, built at Xerox PARC in the 1970s by Alan Kay's group, popularised the term object-oriented and made every value an object.


---

## Module 2: Classes and Objects

*Original URL: https://codekairo.com/notes/oop/classes-and-objects*

### Overview

Quick answer

### What are classes and objects in object-oriented programming?

A class is a user-defined type that declares fields (the data each object holds) and methods (the operations on that data). An object is an instance of a class, created at run time by a constructor, with its own copy of every instance field. Static members belong to the class itself and are shared by all its objects.

- Fields and methods
- Constructors
- this and self
- Static members
- Object lifecycle
- Stack vs heap: what a variable holds
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A class is a type you define yourself: it says what data each object of that type holds and what the object can do. An object is one value of that type, made while the program runs. This note covers what goes inside a class (fields, methods, constructors, destructors, static members), how this and self work, and what actually happens in memory when you create, copy and lose an object — in C++, Java and Python, because each answers those questions differently. If you are new to the idea, start with the Introduction to Object-Oriented Programming .

### Fields and methods

A class has two kinds of member:

- Fields hold state. C++ calls them data members, Python calls them attributes, Java calls them fields or instance variables. Each object gets its own copy of every instance field.
- Methods define behaviour. C++ calls them member functions. A method runs on an object and can read and change that object's fields.

Python is the odd one out: attributes are not declared in the class body. Assigning self.name = name inside a method creates the attribute on that object, and you can even add attributes to one object later — which is why a typo such as self.nmae = ... silently creates a new attribute instead of failing.

### Constructors

A constructor runs once, automatically, when an object is created, and its job is to leave the object in a valid state. It has no return type — in Java, void Student() is an ordinary method that happens to share the class's name, not a constructor.

### Default constructor

A default constructor takes no arguments. If you declare no constructor at all, C++ and Java supply one. In Java, any field no constructor sets holds 0 , false or null ; C++'s generated constructor leaves built-in members such as int uninitialised unless the class gives them a default. The moment you declare any constructor yourself, that free default disappears, so new Student() stops compiling until you write one (in C++ you can ask for it back with Student() = default; ).

### Parameterised constructor

A parameterised constructor takes the starting values as arguments. C++ and Java allow several constructors with different parameter lists (constructor overloading ). Python and JavaScript allow only one constructor per class — a second __init__ simply replaces the first — so they use default argument values instead.

### Copy constructor

A copy constructor builds a new object from an existing one of the same class. C++ generates one for you that copies each member; you write your own when a plain member-by-member copy is wrong, typically when the class owns a raw pointer. Java generates none: a "copy constructor" such as Student(Student other) is just a convention you write by hand. Python uses copy.copy , or a class method that plays the same part. Object Equality, Hashing and Copying goes deeper into shallow and deep copies.

Here are all three, plus a static counter of how many students have been created:

```
#
include
<iostream>
#
include
<string>
using
namespace
std
;
class
Student
{
string name
;
int
roll
;
static
int
count
;
// one copy shared by every Student
public
:
Student
(
)
:
name
(
"Unknown"
)
,
roll
(
0
)
{
count
++
;
}
// default
Student
(
string name
,
int
roll
)
:
name
(
name
)
,
roll
(
roll
)
{
count
++
;
}
// parameterised
Student
(
const
Student
&
other
)
:
name
(
other
.
name
)
,
roll
(
other
.
roll
)
{
count
++
;
}
// copy
void
rename
(
const
string
&
name
)
{
this
->
name
=
name
;
}
// this-> is the field
void
describe
(
)
const
{
cout
<<
roll
<<
" "
<<
name
<<
"\n"
;
}
static
int
created
(
)
{
return
count
;
}
// no this: belongs to the class
}
;
int
Student
::
count
=
0
;
// the static member is defined once, outside the class
int
main
(
)
{
Student a
;
// default constructor
Student
b
(
"Meera"
,
42
)
;
// parameterised constructor
Student c
=
b
;
// copy constructor
c
.
rename
(
"Meera (copy)"
)
;
a
.
describe
(
)
;
b
.
describe
(
)
;
c
.
describe
(
)
;
cout
<<
"Students created: "
<<
Student
::
created
(
)
<<
"\n"
;
return
0
;
}
```

Output

```
0 Unknown
42 Meera
42 Meera (copy)
Students created: 3
```

No arguments, so the default constructor runs and fills in "Unknown" and 0. The object gets its own name and roll; the class's single count goes to 1.

- No arguments, so the default constructor runs and fills in "Unknown" and 0. The object gets its own name and roll; the class's single count goes to 1.
- Two arguments pick the parameterised constructor. b gets its own fields, and the same shared count, the only copy there is, goes to 2.
- Initialising c from b calls the copy constructor: a new object with b's values copied in, not a second name for b. Every constructor adds one, so count is 3.
- Inside rename, this points at c, so this->name is c's field. b keeps "Meera" because the two objects share no fields.
- One describe() method serves all three objects. Each call runs the same code with this pointing at a different object, so each prints its own roll and name.
- created() is static: it is called on the class, has no this, and reads the one shared count, 3. It could not read name or roll, because there is no object to read them from.

Two details worth saying in an interview. Java's this("Unknown", 0) and C++'s delegating constructors ( Student() : Student("Unknown", 0) {} , since C++11) let one constructor reuse another, so the validation lives in one place. And Python splits creation in two: __new__ allocates and returns the new object, then __init__ initialises it. You almost never override __new__ ; it matters for immutable types and singletons.

### this and self

Inside a method, the object the method was called on is available as this (C++, Java, JavaScript) or self (Python). Its main uses:

- Telling a field from a parameter with the same name: this.name = name .
- Passing the current object to another object: registry.add(this) .
- Returning the object for chaining : return *this; in C++ or return this; in Java lets you write builder.setA(1).setB(2) .
- Calling another constructor : this(...) in Java.

In C++, this is a pointer, so you write this->name ; inside a const method it points to a const object. In Python self is not a keyword at all — it is simply the first parameter, and b.describe() is shorthand for Student.describe(b) . Static methods have no this or self , which is why they cannot read instance fields.

### Static members

A static field has one copy for the whole class instead of one per object — a counter of objects created, a shared configuration value, a cache. A static method belongs to the class and is called through it: Student.created() , Math.max(a, b) .

- C++ : declare static int count; inside the class and define it once outside ( int Student::count = 0; ), or write inline static int count = 0; since C++17.
- Java : static fields and methods; a static { ... } block runs once when the class is initialised. Static methods are not overridden — a subclass's static method with the same signature hides the parent's.
- Python : a variable in the class body is a class attribute. @staticmethod receives neither object nor class; @classmethod receives the class as cls , so it works correctly for subclasses and is the usual way to write alternative constructors.

The classic Python trap is self.count += 1 :

In the first object's initialiser, self.count is read first: the object has no count, so the lookup falls through to the class and finds 0. The += then writes count = 1 onto the object, not the class.

- In the first object's initialiser, self.count is read first: the object has no count, so the lookup falls through to the class and finds 0. The += then writes count = 1 onto the object, not the class.
- Every object does the same, so after three students each has a private count of 1 and the class's count is still 0. The shared counter never moved.
- Writing to the class by name, Student.count += 1, changes the one shared attribute: 3 after three students, and no object has a count of its own.

Write Student.count += 1 (or type(self).count += 1 ).

### Object lifecycle

Every object goes through the same stages:

- Allocation — memory for the fields is reserved (stack or heap).
- Initialisation — the constructor runs.
- Use — methods are called on it.
- End of life — in C++, the scope ends or delete is called; in Java and Python, the object becomes unreachable.
- Clean-up and deallocation — a destructor or finaliser may run, then the memory is returned.

Steps 4 and 5 are where the languages differ most:

C++ destructors run in the reverse order of construction , which is what makes them safe for releasing resources. This program traces every construction and destruction:

```
#
include
<iostream>
#
include
<memory>
#
include
<string>
using
namespace
std
;
class
Tracer
{
string name
;
public
:
Tracer
(
string n
)
:
name
(
n
)
{
cout
<<
"construct "
<<
name
<<
"\n"
;
}
~
Tracer
(
)
{
cout
<<
"destroy "
<<
name
<<
"\n"
;
}
}
;
Tracer
global
(
"global"
)
;
// static storage: built before main, destroyed after it
int
main
(
)
{
cout
<<
"main starts\n"
;
Tracer
a
(
"a"
)
;
{
Tracer
b
(
"b"
)
;
Tracer
c
(
"c"
)
;
cout
<<
"inner scope ends\n"
;
}
// c, then b: reverse order of construction
Tracer
*
raw
=
new
Tracer
(
"heap"
)
;
// heap: lives until delete
unique_ptr
<
Tracer
>
owned
=
make_unique
<
Tracer
>
(
"owned"
)
;
// freed by its owner
delete
raw
;
cout
<<
"main ends\n"
;
return
0
;
}
// owned, then a; global after main returns
```

Output

```
construct global
main starts
construct a
construct b
construct c
inner scope ends
destroy c
destroy b
construct heap
construct owned
destroy heap
main ends
destroy owned
destroy a
destroy global
```

Tracer global is a global, in static storage: it is constructed before main runs, so its line is printed first.

- Tracer global is a global, in static storage: it is constructed before main runs, so its line is printed first.
- main starts and declares a, a local object: its storage is part of main's stack frame, and its constructor runs at the declaration.
- The braces open an inner scope. b and c are constructed in the order they are declared, inside that scope.
- At the closing brace the inner scope's locals die in the reverse order of construction: c first, then b. Nothing else is touched.
- new puts a Tracer on the heap and raw holds only its address; make_unique does the same but hands ownership to the unique_ptr owned.
- delete raw destroys the heap object at once. raw still holds the old address, now dangling; forgetting this line would have leaked the object.
- main returns, and its locals die in reverse order: owned's destructor deletes the object it owns, then a is destroyed. A raw pointer's destruction does nothing.
- Last, after main has returned, the static object is destroyed. Every object's end of life is a line of the program you can point at.

A raw heap object leaks until someone deletes it. That is why modern C++ wraps heap objects in unique_ptr or shared_ptr , whose destructors do the delete . Java and Python cannot show this trace reliably, which is exactly the point — their clean-up is not tied to a line of code. The Java and Python answers for deterministic clean-up are covered in Exception Handling in OOP .

### Stack vs heap: what a variable holds

The most useful mental model for interviews is not "stack or heap" but what does the variable hold — the object, or a reference to it?

So b = a means two very different things:

In Java and Python the object is created on the heap and the variable a holds only a reference to it, drawn as an arrow.

- In Java and Python the object is created on the heap and the variable a holds only a reference to it, drawn as an arrow.
- b = a copies the reference, not the object. There is still one Point, now with two arrows into it: b is a second name for the same object.
- Writing through b changes the one object, so reading through a sees it too: a.x is 10. This sharing is called aliasing.
- A real copy has to be asked for — a copy constructor, or copy.copy in Python. It builds a second object with the same values, and c refers to that one.
- Changing the copy leaves the original alone: c.x is 99 while a.x stays 10. Two objects now, three variables.
- C++ by default stores the object in the variable itself. Point& b = a gives Java-style sharing, while Point c = a copies the whole object into c, so the same output needs no new.

The C++ program below uses a reference ( Point& ) to get Java-style sharing, then a plain variable to get a copy:

```
#
include
<iostream>
using
namespace
std
;
struct
Point
{
int
x
,
y
;
}
;
int
main
(
)
{
Point a
{
1
,
2
}
;
Point
&
b
=
a
;
// b is another name for a: what Java and Python variables do
b
.
x
=
10
;
cout
<<
"after b.x = 10: a.x = "
<<
a
.
x
<<
"\n"
;
Point c
=
a
;
// a C++ variable holds the object itself, so this copies it
c
.
x
=
99
;
cout
<<
"after c.x = 99: a.x = "
<<
a
.
x
<<
", c.x = "
<<
c
.
x
<<
"\n"
;
return
0
;
}
```

Output

```
after b.x = 10: a.x = 10
after c.x = 99: a.x = 10, c.x = 99
```

The same rule explains parameter passing. Java and Python pass the reference by value : a method can change the object it was given, but assigning a new object to the parameter does not affect the caller's variable. C++ copies the whole object unless the parameter is a reference ( const Student& ) or a pointer.

### Common mistakes

- Writing a return type on a constructor ( void Student() in Java), which turns it into an ordinary method.
- Declaring a parameterised constructor and then calling new Student() , expecting the default one to still exist.
- Using self.count += 1 for a shared counter in Python, which creates an instance attribute instead.
- Expecting Java's finalize() or Python's __del__ to run at a predictable time; use try-with-resources or with .
- Forgetting that b = a in C++ copies the object, while in Java and Python it only copies the reference.
- Taking a C++ copy constructor's parameter by value instead of const T& .

### Interview questions

What is the difference between a constructor and a method? A constructor has no return type, is called automatically exactly once when the object is created, and exists to initialise it. A method has a return type and can be called any number of times on an existing object. Constructors are also not inherited in Java; C++ can opt in with using Base::Base; .

Why must a C++ copy constructor take its argument by reference? Passing an object by value itself calls the copy constructor, so a copy constructor that took its argument by value would have to call itself to receive the argument, without end. The language therefore rejects that signature. The parameter is const T& so it can also accept temporaries and const objects.

When does C++ call the copy constructor, and when the copy assignment operator? The copy constructor runs when a new object is initialised from an existing one: Student c = b; , Student c(b); , passing by value, and returning by value when the copy is not elided. The copy assignment operator runs when an already existing object is overwritten: c = b; on a c that was constructed earlier.

Can a constructor be private? Why would you do that? Yes, in C++ and Java. A private constructor stops other code from creating objects directly, which is how a Singleton controls its single instance, how a class forces callers through a static factory method, and how a utility class such as one holding only static methods prevents instantiation.

What is the size of an object of an empty class in C++? It is at least 1 byte, never 0, so that two distinct objects always have distinct addresses. When an empty class is used as a base class, the compiler may give it zero bytes inside the derived object (the empty base optimisation).

Does Java have destructors? What replaces them? No. The garbage collector frees memory at a time of its choosing, and finalize() was deprecated in Java 9 and deprecated for removal in Java 18. For files, sockets and locks, implement AutoCloseable and use try-with-resources; java.lang.ref.Cleaner exists as a last-resort safety net.

What is the difference between __new__ and __init__ in Python? __new__ is a static method that creates and returns the new instance; __init__ receives that instance as self and initialises it, returning nothing. You override __new__ only when you must control creation itself — subclassing an immutable type like tuple , or returning an existing instance.

What is the difference between a class method and a static method in Python? A @classmethod receives the class as its first argument ( cls ), so cls(...) builds an object of whichever subclass it was called on — ideal for alternative constructors. A @staticmethod receives nothing extra; it is a plain function kept in the class's namespace.

Next, read Encapsulation , then check yourself with the OOP Basic skill test .

### What is a constructor in OOP?

A constructor is a special method that runs automatically when an object is created and puts its fields into a valid starting state. In C++ and Java it has the same name as the class and no return type; in Python it is the __init__ method.

### What are the types of constructors?

The usual three are the default constructor (no arguments), the parameterised constructor (takes the starting values) and the copy constructor (builds a new object from an existing one). C++ also has move constructors, and Java and C++ let a class declare several constructors with different parameter lists.

### What is the difference between static and non-static members?

A non-static (instance) field has one copy per object, and an instance method runs on a particular object through this or self. A static field has one copy for the whole class, and a static method runs without any object, so it cannot touch instance fields directly.

### Are objects stored on the stack or the heap?

In C++ either: a local object lives on the stack and dies at the end of its scope, while an object made with new lives on the heap until it is deleted. In Java and Python objects live on the heap and variables hold references to them.

### What is a destructor?

A destructor is a C++ member function named ~ClassName that runs automatically at the exact moment an object's lifetime ends, to release what it owns. Java has no destructors; its garbage collector frees memory at an unspecified time. Python's __del__ is a finaliser whose timing depends on the implementation.


---

## Module 3: Encapsulation

*Original URL: https://codekairo.com/notes/oop/encapsulation*

### Overview

Quick answer

### What is encapsulation in OOP?

Encapsulation is bundling an object's data together with the methods that operate on it, and restricting direct access to that data so it can change only through those methods. It lets a class enforce its own rules — a balance that never goes negative, a mark between 0 and 100 — and change its internals without breaking the code that uses it.

- What encapsulation means
- Access modifiers in C++, Java and Python
- Getters and setters with validation
- Immutable classes
- Encapsulation vs abstraction vs data hiding
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Encapsulation is the first pillar of OOP and the one that does the most everyday work. A class bundles its data with the methods that use that data, and it hides the data so that nothing outside the class can change it except through those methods. The payoff is that the class can promise things about its own state — "the stock is never negative", "the email always contains an @" — and keep the promise, because every change goes through code it controls. This note covers how C++, Java and Python each restrict access, how to write setters that actually protect something, and how to build immutable classes.

### What encapsulation means

Encapsulation has two parts:

- Bundling — the data and the operations on it live in one class, so the rules about the data live next to it.
- Access restriction (data hiding) — fields are made inaccessible from outside, and the class offers methods as the only way in.

The rules a class keeps true about its own state are called invariants . A Product might have two: price is positive, stock is not negative. If stock were a public field, any line anywhere could set it to −5 and the invariant would be gone. With the field private, only the class's methods can change it, and each method checks the rule.

Encapsulation pays off in three ways:

- Correctness — invariants are checked in one place instead of at every call site.
- Freedom to change — callers depend on methods, not fields, so you can store a price in paise instead of rupees, or cache a computed value, without touching any caller.
- Easier debugging — when a value goes wrong, there are only a few methods that could have changed it.

### C++

C++ has three access specifiers, written as labels inside the class:

- public — anyone can use the member.
- protected — the class itself, classes derived from it, and its friends.
- private — the class itself and its friends only.

Members of a class are private until a label says otherwise; members of a struct are public. A class can grant access to a named function or class with friend — the class decides who its friends are, so this does not let outside code break in uninvited.

### Java

Java has four levels, one of them without a keyword:

private: only Product's own code, such as sell(), may touch stock. Inventory, the subclass and Main all fail to compile, which is what lets Product keep its invariant.

- private: only Product's own code, such as sell(), may touch stock. Inventory, the subclass and Main all fail to compile, which is what lets Product keep its invariant.
- With no modifier, Java opens the member to every class in package shop, so Inventory compiles too. Code in another package, even a subclass, still cannot see it.
- protected adds subclasses in other packages, through their own type: SalePen can use the stock it inherits. Java's protected also keeps the whole package, which C++'s does not.
- public removes the wall: all 4 kinds of code can read and write stock, including Main, and Product can no longer promise anything about its value.

One detail trips people up: a subclass in another package can use an inherited protected member only through references of its own type, not through an arbitrary parent-class object. A top-level class can only be public or package-private.

### Python

Python has no access keywords. It relies on naming conventions:

- name — public.
- _name — internal; please do not use it from outside. Nothing stops you.
- __name (two leading underscores, at most one trailing) — name mangling : inside class Account , self.__pin is stored as self._Account__pin . The goal is to stop a subclass accidentally overwriting the attribute, not security; obj._Account__pin still works.

Python's tool for controlled access is @property , which makes a method look like an attribute. Callers write p.price = 25 , and the property's setter runs and can reject the value.

### Side by side

In C++ and Java, access is checked per class, not per object : a method of Account may read the private balance of another Account object. That is what makes equals(Account other) and copy constructors possible.

### Getters and setters with validation

A getter returns a field's value; a setter changes it. A setter earns its place only if it checks something. Better still, give the class methods that describe real operations — sell(quantity) rather than setStock(getStock() - quantity) — a guideline often called tell, don't ask . The class below rejects invalid prices and stock levels, and sell refuses to oversell:

```
#
include
<iostream>
#
include
<stdexcept>
#
include
<string>
using
namespace
std
;
class
Product
{
string name
;
int
price
;
// rupees; invariant: > 0
int
stock
;
// invariant: >= 0
public
:
Product
(
string name
,
int
price
,
int
stock
)
:
name
(
name
)
,
price
(
0
)
,
stock
(
0
)
{
setPrice
(
price
)
;
// the constructor uses the same checks
setStock
(
stock
)
;
}
int
getPrice
(
)
const
{
return
price
;
}
void
setPrice
(
int
p
)
{
if
(
p
<=
0
)
throw
invalid_argument
(
"price must be positive"
)
;
price
=
p
;
}
void
setStock
(
int
s
)
{
if
(
s
<
0
)
throw
invalid_argument
(
"stock cannot be negative"
)
;
stock
=
s
;
}
void
sell
(
int
qty
)
{
// an operation, not a raw setter
if
(
qty
>
stock
)
throw
invalid_argument
(
"only "
+
to_string
(
stock
)
+
" in stock"
)
;
stock
-=
qty
;
}
void
show
(
)
const
{
cout
<<
name
<<
": Rs "
<<
price
<<
", stock "
<<
stock
<<
"\n"
;
}
}
;
int
main
(
)
{
Product
pen
(
"Pen"
,
20
,
100
)
;
pen
.
show
(
)
;
try
{
pen
.
setPrice
(
-
5
)
;
}
catch
(
const
invalid_argument
&
e
)
{
cout
<<
"rejected: "
<<
e
.
what
(
)
<<
"\n"
;
}
try
{
pen
.
setStock
(
-
1
)
;
}
catch
(
const
invalid_argument
&
e
)
{
cout
<<
"rejected: "
<<
e
.
what
(
)
<<
"\n"
;
}
pen
.
sell
(
30
)
;
try
{
pen
.
sell
(
500
)
;
}
catch
(
const
invalid_argument
&
e
)
{
cout
<<
"rejected: "
<<
e
.
what
(
)
<<
"\n"
;
}
pen
.
setPrice
(
25
)
;
pen
.
show
(
)
;
return
0
;
}
```

Output

```
Pen: Rs 20, stock 100
rejected: price must be positive
rejected: stock cannot be negative
rejected: only 70 in stock
Pen: Rs 25, stock 70
```

The constructor runs the same setPrice and setStock checks as everyone else, so pen starts valid: price 20, stock 100. An invalid Product can never be created.

- The constructor runs the same setPrice and setStock checks as everyone else, so pen starts valid: price 20, stock 100. An invalid Product can never be created.
- Outside code cannot reach a private field at all: this line does not compile. The public methods on the object's edge are the only way in, and each one checks before it writes.
- setPrice(-5) fails its check and throws before the assignment, so price is still 20. A failed call leaves the object exactly as it was.
- setStock(-1) is refused the same way: stock stays 100, because stock may never be negative.
- sell(30) is an operation, not a raw setter: it checks there is enough stock, then writes 100 − 30 = 70 itself.
- sell(500) asks for more than the 70 in stock, so sell refuses and says why. The caller never had to check; the rule lives in one place.
- A valid price goes through: price becomes 25. Of the six calls, three were refused, and stock and price kept their rules after every one.

### Immutable classes

An immutable object cannot change after it is built. Immutable objects are simple to reason about, safe to share between threads without locks, and safe to use as keys in hash maps. Java's String , Integer and LocalDate , and Python's str , int , tuple and frozenset , are all immutable.

The recipe, in Java terms:

- Make every field private final and set each one in the constructor.
- Provide no setters. Methods that "change" the object return a new object instead ( plus , withPrice ).
- Make the class final , so no subclass can add mutable state or override methods to behave mutably.
- Make defensive copies of mutable inputs (a list passed to the constructor) and never hand out a mutable internal object.

Java 16's record covers rules 1–3 in one line, though a record holding a List is only as immutable as that list. In Python, @dataclass(frozen=True) makes assignment to a field raise an error, and storing a tuple instead of a list covers rule 4. In C++, const member functions promise not to change the object, const objects can call only those, and value members are copied on construction automatically.

```
#
include
<iostream>
#
include
<iomanip>
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
class
Money
{
// immutable: private state, no setters, const methods only
const
long
paise
;
const
string currency
;
public
:
Money
(
long
paise
,
string currency
)
:
paise
(
paise
)
,
currency
(
currency
)
{
}
Money
plus
(
const
Money
&
other
)
const
{
return
Money
(
paise
+
other
.
paise
,
currency
)
;
}
void
show
(
const
string
&
label
)
const
{
cout
<<
label
<<
": "
<<
currency
<<
" "
<<
paise
/
100
<<
"."
<<
setw
(
2
)
<<
setfill
(
'0'
)
<<
paise
%
100
<<
"\n"
;
}
}
;
class
Roster
{
const
vector
<
string
>
names
;
// stored by value: the caller's vector is copied
public
:
explicit
Roster
(
const
vector
<
string
>
&
names
)
:
names
(
names
)
{
}
size_t
size
(
)
const
{
return
names
.
size
(
)
;
}
}
;
int
main
(
)
{
Money
price
(
49950
,
"INR"
)
;
Money total
=
price
.
plus
(
Money
(
5025
,
"INR"
)
)
;
// a new object; price is untouched
price
.
show
(
"price"
)
;
total
.
show
(
"total"
)
;
vector
<
string
>
input
=
{
"Asha"
,
"Ravi"
}
;
Roster
roster
(
input
)
;
input
.
push_back
(
"Kiran"
)
;
// changing the caller's vector
cout
<<
"roster size: "
<<
roster
.
size
(
)
<<
"\n"
;
return
0
;
}
```

Output

```
price: INR 499.50
total: INR 549.75
roster size: 2
```

price refers to a Money of 49950 paise, INR 499.50. Its fields are private and final, and Money has no setters, so this object will hold that amount for as long as it exists.

- price refers to a Money of 49950 paise, INR 499.50. Its fields are private and final, and Money has no setters, so this object will hold that amount for as long as it exists.
- plus does not add into price. It builds a third object holding 49950 + 5025 = 54975 paise, and price still reads INR 499.50 while total reads INR 549.75.

The constructor copies the caller's list, so the roster's field refers to a list nobody else holds. Two references, two lists.

- The constructor copies the caller's list, so the roster's field refers to a list nobody else holds. Two references, two lists.
- The caller adds Kiran to its own list, which now holds 3 names. The roster's copy is untouched and size() still says 2, as the note's program prints.
- Without the copy, the field is one more reference to the caller's list, and the same add changes the "immutable" roster behind its back: size() says 3.

A missing defensive copy is the most common way an "immutable" class turns out not to be.

### Encapsulation vs abstraction vs data hiding

Abstraction gets its own note: Abstraction: Abstract Classes and Interfaces .

### Common mistakes

- Generating a getter and setter for every private field; a setter with no checks is a public field with extra steps.
- Returning an internal mutable list from a getter, so callers can modify it behind the class's back.
- Believing Python's __name makes an attribute private; it only renames it.
- Assuming Java's protected means "subclasses only"; it also opens the member to the whole package.
- Validating in setters but not in the constructor, so invalid objects can still be created.
- Marking fields final and calling the class immutable while a field holds a mutable list.

### Interview questions

How do you achieve encapsulation in Java? Declare the fields private , expose behaviour through public methods that validate their input, and keep helper classes package-private. Packages, and since Java 9 modules, extend the same idea to whole groups of classes by choosing which ones other code can see.

Can a method read the private fields of another object of the same class? Yes, in both C++ and Java access control is per class, not per object. A method of Account may read other.balance when other is also an Account . This is what lets you write copy constructors, equals methods and comparison operators.

What is name mangling in Python, and does it make an attribute private? An attribute written __pin inside class Account is stored as _Account__pin . It exists to prevent accidental clashes when a subclass uses the same name. It is not privacy: obj._Account__pin still reads it.

How does protected differ between C++ and Java? In C++, a protected member is visible to the class, its derived classes and friends. In Java it is also visible to every class in the same package, whether or not it is a subclass. Java subclasses in other packages may use it only through their own type.

Why should an immutable class be final in Java? A subclass could add mutable fields or override methods so that its objects appear to change, and code holding a reference of the parent type would be fooled. Making the class final , or making the constructor private and offering a static factory, closes that hole.

Is a C++ friend function a violation of encapsulation? Not necessarily. The class itself names its friends, so access is still granted deliberately and in one place. A friend is best seen as part of the class's interface — operator<< for printing is the common example. Granting friendship widely does weaken the class's guarantees.

Can Java reflection access private fields? Yes: Field.setAccessible(true) lets code read and write private fields of ordinary classes. Since Java 9 the module system can block this for packages a module does not open, and the JDK's own internals have been blocked by default since Java 16. Access modifiers guard against mistakes, not against hostile code in the same process.

Are getters and setters always good practice? No. They are better than public fields because they leave room for validation and change, but a class made of nothing else is a data holder whose rules live elsewhere. Prefer methods that perform meaningful operations and keep the rules inside the class.

Next, read Inheritance , then check yourself with the OOP Basic skill test .

### What is the difference between encapsulation and data hiding?

Data hiding is the access-restriction part: making fields private so outside code cannot touch them. Encapsulation is the wider idea of bundling data with the methods that use it, with data hiding as the tool that makes the bundle trustworthy. Many textbooks use the two words almost interchangeably.

### What is the difference between encapsulation and abstraction?

Encapsulation is about protecting an object's data by bundling it with methods and hiding it behind access control. Abstraction is about exposing only what an object does and hiding how it does it, usually through interfaces or abstract classes. Encapsulation hides data; abstraction hides complexity.

### Does Python support private variables?

Not in the enforced sense. A single leading underscore (_balance) marks an attribute as internal by convention, and a double leading underscore (__balance) triggers name mangling to _ClassName__balance, which avoids clashes in subclasses. Any code can still reach either one; Python relies on programmers respecting the convention.

### What is the default access modifier in Java?

When you write no modifier, a member is package-private: visible to every class in the same package and to nothing outside it, not even subclasses in other packages. There is no keyword for it, so it is often called default access. Interface members are the exception: they are public by default.

### Why do we use getters and setters?

They let a class control how a field is read and changed: a setter can validate the new value, a getter can compute or copy what it returns, and the field's storage can change later without changing callers. A setter that accepts anything, though, protects nothing; prefer methods that express real operations.

### What is an immutable class?

An immutable class is one whose objects cannot change after construction: all fields are set in the constructor, none has a setter, and any method that seems to modify the object returns a new one instead. Java's String and Integer and Python's str and tuple are immutable.


---

## Module 4: Abstraction: Abstract Classes and Interfaces

*Original URL: https://codekairo.com/notes/oop/abstraction*

### Overview

Quick answer

### What is abstraction in object-oriented programming?

Abstraction means exposing what an object does while hiding how it does it, so callers depend on a small contract instead of on implementation details. In code it is written as abstract classes, which mix declared and implemented methods, and interfaces, which list methods any class can promise to provide. Callers are written against the abstract type, and implementations can change freely.

- What abstraction means
- Abstraction vs encapsulation
- Abstract classes
- Interfaces
- Abstract class and interface together
- Abstract class vs interface
- When to use which
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Abstraction is the pillar that decides what a caller needs to know. When you call payment.pay(499) , you need to know that the money moves and a receipt appears — not whether it went through a UPI app, a card network or a wallet. Hiding the "how" behind a small "what" lets each side change independently: new payment methods arrive without touching checkout code, and checkout changes without touching payment code. This note shows how C++, Java and Python write abstractions down as abstract classes and interfaces , and how to choose between them.

### What abstraction means

Every working system is layered abstractions. You drive a car through a steering wheel and pedals, not by controlling fuel injection. A programmer calls sort(list) without knowing whether it is a merge sort or a Timsort. In OOP, an abstraction is a contract : a set of method signatures plus the promised behaviour, independent of any implementation.

The rule that makes abstraction useful is program to an interface, not an implementation : declare variables, parameters and return types with the abstract type ( PaymentMethod , List , Shape ) and create concrete objects ( UpiPayment , ArrayList , Circle ) in as few places as possible.

### Abstraction vs encapsulation

These two are the most often confused pair in OOP interviews.

They work together: abstraction designs the outside of an object, and encapsulation protects its inside. Encapsulation has its own note.

### Abstract classes

An abstract class cannot be instantiated. It is a partial class — some methods written, some only declared — meant to be completed by subclasses. It may have fields, constructors and ordinary methods. A subclass must implement every abstract method, or it is abstract too.

### C++: pure virtual functions

C++ has no abstract keyword. A class is abstract if it has at least one pure virtual function , declared with = 0 , as in virtual int area() const = 0; . Give such a class a virtual destructor too ( virtual ~Shape() = default; ), so that deleting a derived object through a Shape* runs the derived destructor. A derived class that does not override every pure virtual function it inherits is itself abstract.

A pure virtual function can still have a body, defined outside the class and called explicitly as Shape::area() ; a pure virtual destructor must have one, because derived destructors always call it.

### Java: the abstract keyword

abstract class Shape with abstract int area(); . A Java class can be declared abstract even with no abstract methods, purely to forbid instantiation. An abstract method cannot be private , static or final , since each of those makes overriding impossible, and a class cannot be both abstract and final .

### Python: abstract base classes

Inherit from abc.ABC and decorate required methods with @abstractmethod . The check happens when you create an object , not when you define the class: defining an incomplete subclass is fine, instantiating it raises TypeError . An ABC with no abstract methods can be instantiated normally.

```
from
abc
import
ABC
,
abstractmethod
class
Shape
(
ABC
)
:
@abstractmethod
def
area
(
self
)
:
.
.
.
class
Square
(
Shape
)
:
def
__init__
(
self
,
side
)
:
self
.
side
=
side
def
area
(
self
)
:
return
self
.
side
*
self
.
side
class
Blob
(
Shape
)
:
# forgot to implement area()
pass
for
make
in
(
lambda
:
Shape
(
)
,
lambda
:
Blob
(
)
,
lambda
:
Square
(
3
)
)
:
try
:
shape
=
make
(
)
print
(
f"
{
type
(
shape
)
.
__name__
}
: created, area
{
shape
.
area
(
)
}
"
)
except
TypeError
:
print
(
"TypeError: the class is still abstract"
)
print
(
sorted
(
Shape
.
__abstractmethods__
)
)
```

Output

```
TypeError: the class is still abstract
TypeError: the class is still abstract
Square: created, area 9
['area']
```

Python checks when you create an object, not when you define the class. Shape's own area() is marked abstract, so Shape() raises TypeError.

- Python checks when you create an object, not when you define the class. Shape's own area() is marked abstract, so Shape() raises TypeError.
- Blob defines nothing, so looking up area along its MRO (Blob, Shape, ABC) finds Shape's abstract version first. Defining Blob was fine; creating one raises TypeError.
- Square's own area() is found before Shape's, so nothing abstract remains and Square(3) is created; its area is 3 × 3 = 9.

### Interfaces

An interface is a pure contract: a list of methods a class promises to provide, usually with no state. A class that implements an interface can be used anywhere that interface type is expected, whatever else the class is.

### Java interfaces

Java's interface keyword has grown over the years:

- Abstract methods — the default for a method without a body; implicitly public abstract .
- Constants — every field is implicitly public static final . There are no instance fields.
- Default methods (Java 8) — a method with a body that implementing classes inherit and may override. They were added so existing interfaces could gain methods — forEach on Iterable , stream on Collection — without breaking every class that already implemented them.
- Static methods (Java 8) — helpers called on the interface itself, such as Comparator.naturalOrder() .
- Private methods (Java 9) — helpers shared by the default methods, invisible to implementers.

A class may implement many interfaces, and an interface may extend many interfaces. An interface with exactly one abstract method is a functional interface and can be implemented with a lambda. An interface with no methods at all, such as Serializable , is a marker interface .

```
interface
Discount
{
int
CAP_PERCENT
=
50
;
// implicitly public static final
int
percent
(
)
;
// implicitly public abstract
default
int
apply
(
int
price
)
{
// Java 8: implementers inherit this body
return
price
-
price
*
capped
(
)
/
100
;
}
private
int
capped
(
)
{
// Java 9: a helper for the default method only
return
Math
.
min
(
percent
(
)
,
CAP_PERCENT
)
;
}
static
Discount
none
(
)
{
// Java 8: called on the interface itself
return
(
)
->
0
;
// one abstract method, so a lambda can implement it
}
}
class
FestiveDiscount
implements
Discount
{
public
int
percent
(
)
{
return
70
;
}
// above the cap
}
public
class
Main
{
public
static
void
main
(
String
[
]
args
)
{
System
.
out
.
println
(
"festive price: "
+
new
FestiveDiscount
(
)
.
apply
(
1000
)
)
;
System
.
out
.
println
(
"no discount: "
+
Discount
.
none
(
)
.
apply
(
1000
)
)
;
System
.
out
.
println
(
"cap: "
+
Discount
.
CAP_PERCENT
+
"%"
)
;
}
}
```

Output

```
festive price: 500
no discount: 1000
cap: 50%
```

An interface lists one abstract method every implementer must write, and since Java 8 and 9 it can also carry a default body, a private helper for it, a static factory and constants. It never holds per-object state.

- An interface lists one abstract method every implementer must write, and since Java 8 and 9 it can also carry a default body, a private helper for it, a static factory and constants. It never holds per-object state.
- new FestiveDiscount().apply(1000) runs the inherited default apply(), which calls the private capped(), which calls percent() on the object: 70, capped at 50. The price is 1000 − 1000 × 50 / 100 = 500.
- The static none() is called on the interface itself and returns a lambda: percent() is the only abstract method, so () -> 0 implements the whole interface. Its apply(1000) gives 1000.

### C++ and Python interfaces

C++ has no interface keyword; an interface is a class with only pure virtual functions and a virtual destructor. Because such a class has no data, inheriting several of them is the safe kind of multiple inheritance. Python writes an interface as an ABC whose methods are all abstract, or — since Python 3.8 — as a typing.Protocol , which a class satisfies simply by having the right methods (structural typing, checked by type checkers rather than at run time). And in everyday Python, duck typing means an interface often exists only in the documentation.

### Abstract class and interface together

Real designs often use both: an interface names a capability and an abstract class shares an implementation . Every payment method below follows the same pay steps, written once in the abstract class; only some can be refunded, so that capability is a separate interface.

PaymentMethod is abstract: it has state (owner), a constructor and a finished pay(), and leaves charge() to subclasses. Refundable is an interface, a single promise. UpiPayment extends one and implements the other; CardPayment only extends.

- PaymentMethod is abstract: it has state (owner), a constructor and a finished pay(), and leaves charge() to subclasses. Refundable is an interface, a single promise. UpiPayment extends one and implements the other; CardPayment only extends.
- The checkout code depends only on the two abstractions: it calls pay() on a PaymentMethod and refund() on a Refundable. A new payment class can arrive without a line of checkout changing.

```
#
include
<iostream>
#
include
<memory>
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
class
Refundable
{
// an interface: pure virtual functions only
public
:
virtual
~
Refundable
(
)
=
default
;
virtual
void
refund
(
int
amount
)
=
0
;
}
;
class
PaymentMethod
{
// an abstract class: state, a constructor, concrete and pure virtual methods
protected
:
string owner
;
virtual
void
charge
(
int
amount
)
=
0
;
// each subclass decides how
public
:
explicit
PaymentMethod
(
string owner
)
:
owner
(
owner
)
{
}
virtual
~
PaymentMethod
(
)
=
default
;
void
pay
(
int
amount
)
{
// the same steps for every payment method
if
(
amount
<=
0
)
{
cout
<<
"rejected: amount must be positive\n"
;
return
;
}
charge
(
amount
)
;
cout
<<
"receipt for "
<<
owner
<<
": Rs "
<<
amount
<<
"\n"
;
}
}
;
class
UpiPayment
:
public
PaymentMethod
,
public
Refundable
{
string handle
;
protected
:
void
charge
(
int
amount
)
override
{
cout
<<
"UPI: charged Rs "
<<
amount
<<
" to "
<<
handle
<<
"\n"
;
}
public
:
UpiPayment
(
string owner
,
string handle
)
:
PaymentMethod
(
owner
)
,
handle
(
handle
)
{
}
void
refund
(
int
amount
)
override
{
cout
<<
"UPI: refunded Rs "
<<
amount
<<
" to "
<<
handle
<<
"\n"
;
}
}
;
class
CardPayment
:
public
PaymentMethod
{
string last4
;
protected
:
void
charge
(
int
amount
)
override
{
cout
<<
"Card: charged Rs "
<<
amount
<<
" to card ending "
<<
last4
<<
"\n"
;
}
public
:
CardPayment
(
string owner
,
string last4
)
:
PaymentMethod
(
owner
)
,
last4
(
last4
)
{
}
}
;
int
main
(
)
{
vector
<
unique_ptr
<
PaymentMethod
>>
methods
;
methods
.
push_back
(
make_unique
<
UpiPayment
>
(
"Asha"
,
"asha@bank"
)
)
;
methods
.
push_back
(
make_unique
<
CardPayment
>
(
"Ravi"
,
"4242"
)
)
;
for
(
auto
&
m
:
methods
)
m
->
pay
(
499
)
;
methods
[
1
]
->
pay
(
0
)
;
for
(
auto
&
m
:
methods
)
// only methods that are also Refundable
if
(
auto
r
=
dynamic_cast
<
Refundable
*
>
(
m
.
get
(
)
)
)
r
->
refund
(
99
)
;
return
0
;
}
```

Output

```
UPI: charged Rs 499 to asha@bank
receipt for Asha: Rs 499
Card: charged Rs 499 to card ending 4242
receipt for Ravi: Rs 499
rejected: amount must be positive
UPI: refunded Rs 99 to asha@bank
```

pay() is written once in PaymentMethod. For Asha's UpiPayment the check passes, and step 2 is a virtual call that lands in UpiPayment::charge, the only part that differs.

- pay() is written once in PaymentMethod. For Asha's UpiPayment the check passes, and step 2 is a virtual call that lands in UpiPayment::charge, the only part that differs.
- The same steps for Ravi's card: only step 2 changes, now running CardPayment::charge. The caller wrote pay(499) both times and never learned which class it held.
- An amount of 0 fails step 1, so charge() is never called. The rule lives in the abstract class, and no subclass can forget it.
- The refund loop asks each object whether it is also a Refundable. Only UpiPayment implements that interface, so only it is refunded; the card is skipped, not broken.

The C++ dynamic_cast here is a cross-cast : it goes sideways from PaymentMethod* to Refundable* , which works because UpiPayment inherits both.

### When to use which

- Use an interface when unrelated classes should share a capability ( Comparable , AutoCloseable ), when a class needs several such capabilities, or when you want callers to depend on the thinnest possible contract.
- Use an abstract class when closely related classes share state or code, when you want to fix the order of steps and let subclasses fill in one of them (the Template Method pattern), or when you need constructors and non-public members.
- When in doubt, publish an interface and add an abstract class that implements part of it as a convenience, as Java's collections do with List and AbstractList .

### Common mistakes

- Defining abstraction as "hiding data"; that is encapsulation. Abstraction hides complexity behind a contract.
- Forgetting the virtual destructor in a C++ abstract base class used through pointers.
- Assuming Python checks abstract methods when the class is defined; it checks when you instantiate.
- Saying Java interfaces cannot contain method bodies; since Java 8 they can, through default and static methods.
- Giving an interface methods that only some implementers can honour, so the rest throw "not supported" — split the interface instead.
- Declaring variables with the concrete type ( ArrayList , UpiPayment ) when the abstract one would do.

### Interview questions

If an abstract class cannot be instantiated, why can it have a constructor? Because objects of its concrete subclasses contain the abstract class's fields, and those fields need initialising. Each subclass constructor calls the abstract class's constructor through super(...) or the initialiser list, so the shared setup and validation are written once.

Can a class be abstract without any abstract methods? In Java, yes: abstract class Base {} simply cannot be instantiated. In C++ a class is abstract only if it has a pure virtual function; a protected constructor is the usual way to prevent direct instantiation otherwise. In Python, an ABC without abstract methods can be instantiated normally.

Can a pure virtual function have a body in C++? Yes. It is defined outside the class and can be called explicitly as Base::f() , often to provide a default that overrides choose to reuse. The class stays abstract. A pure virtual destructor must have a body, because every derived destructor calls it.

Why were default methods added to Java interfaces? To let interfaces evolve. Java 8 needed to add methods like forEach and stream to long-established interfaces such as Iterable and Collection ; a new abstract method would have broken every existing implementation, while a default method gives them a working body for free.

Which modifiers cannot be combined with abstract in Java? final (a final class or method cannot be extended or overridden, while abstract requires it), private (a private method is invisible to subclasses, so it can never be implemented) and static (static methods are not overridden). The compiler reports an illegal combination of modifiers.

What is the difference between abstraction and encapsulation? Abstraction decides what a caller sees — a small contract, with the implementation hidden. Encapsulation decides who can touch an object's data — bundling it with methods and restricting access. An interface is an abstraction tool; private is an encapsulation tool.

What is a marker interface? An interface with no methods, used only to tag a class: Serializable and Cloneable in Java. Code checks for the tag with instanceof , and Object.clone() throws if the class is not Cloneable . Annotations now do the same job more flexibly in newer code.

Can an interface extend a class, or a class extend an interface? No to both. An interface can only extend other interfaces, and a class implements interfaces rather than extending them. A class extends exactly one class (implicitly Object ) and may implement any number of interfaces.

Next, read Association, Aggregation and Composition , then check yourself with the OOP Intermediate skill test .

### What is an abstract class?

An abstract class is a class that cannot be instantiated and exists to be extended. It can hold fields, constructors and fully written methods, alongside abstract methods that have no body and must be implemented by every concrete subclass. It captures what related classes share while leaving the differing steps to them.

### What is an interface in Java?

An interface is a type that lists methods a class promises to provide, declared with the interface keyword. Its methods are public and abstract unless marked default, static or private, and its fields are always public static final constants. A class can implement any number of interfaces but extend only one class.

### Can an abstract class have a constructor?

Yes. You cannot call it with new directly, but every subclass constructor calls it through super(...) in Java or the initialiser list in C++, so it is the natural place to initialise the fields the abstract class declares and to check their values.

### What is a pure virtual function in C++?

A pure virtual function is a virtual function declared with = 0, as in virtual int area() const = 0;. It usually has no body, and any class that declares one, or inherits one without overriding it, is abstract and cannot be instantiated. Concrete derived classes must provide the override.

### How do you create an abstract class in Python?

Inherit from abc.ABC and mark the required methods with the @abstractmethod decorator. Python then refuses to instantiate the class, or any subclass that has not overridden every abstract method, raising TypeError at the moment you try to create the object rather than when the class is defined.

### Can we create an object of an abstract class?

Not directly: new Shape() does not compile in Java or C++ when Shape is abstract, and Python raises TypeError. You can, however, create objects of concrete subclasses and hold them in variables of the abstract type, which is exactly how abstract classes are meant to be used.


---

## Module 5: Inheritance

*Original URL: https://codekairo.com/notes/oop/inheritance*

### Overview

Quick answer

### What is inheritance in object-oriented programming?

Inheritance is the mechanism by which one class, the subclass, acquires the fields and methods of another class, the superclass, and can add to them or override them. It models an is-a relationship — a SavingsAccount is an Account — so code written for the parent also works for every child. C++ and Python allow multiple inheritance of classes; Java allows it only through interfaces.

- The is-a relationship
- Types of inheritance
- Method overriding
- super and the order of construction
- The diamond problem
- When to use inheritance
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Inheritance lets you define a new class as an extension of an existing one. The new class — the subclass , child or derived class — automatically has the fields and methods of the existing class — the superclass , parent or base class — and can add new ones or replace inherited ones. It is how OOP expresses "is a kind of": an ElectricCar is a Car , which is a Vehicle . This note covers the kinds of inheritance and which languages allow which, overriding and super , the order in which constructors run, and the diamond problem in C++, Java and Python.

### The is-a relationship

Inherit only when the child genuinely is a kind of the parent and can be used anywhere the parent is expected. A Car is a Vehicle , so code that takes a Vehicle should work when handed a Car . A Car is not an Engine ; it has one, which is composition, covered in Association, Aggregation and Composition .

A subclass gets every field and method of its parent. Private members are still in the child object — they take up space and the parent's methods use them — but the child's own code cannot touch them directly. Java constructors are not inherited at all; C++ can opt in with using Base::Base; , and Python's __init__ is an ordinary method, so a subclass without its own simply uses the parent's.

C++ also chooses an inheritance access level . With public inheritance (the usual one, and the only one that models is-a), the parent's public members stay public. protected inheritance makes them protected, and private inheritance — the default when you write class Car : Vehicle — makes them private, which is really "implemented in terms of" rather than is-a.

### Types of inheritance

Each hollow triangle points from a child to its parent. The top three need only one parent per class; Multiple gives one class two parents, and Hybrid adds a shared grandparent, the diamond that Java allows only through interfaces.

- Single — one parent, one child: Car extends Vehicle .
- Multilevel — a chain: ElectricCar extends Car extends Vehicle . Each level inherits everything above it.
- Hierarchical — several children share one parent: Car , Bike and Truck all extend Vehicle .
- Multiple — one child with two or more parents: a Copier that is both a Scanner and a Printer .
- Hybrid — a mix of the above. The famous case is the diamond, where two parents share a grandparent.

### Method overriding

Overriding means a subclass provides its own version of an inherited method with the same name and parameters. When the method is called through a parent-type reference, the version that runs is the one belonging to the object's actual class — this is run-time polymorphism, covered fully in Polymorphism .

Java adds one more rule: an override may not declare broader checked exceptions than the method it overrides. In C++, a derived function with the same name but different parameters does not overload the base one — it hides every base function of that name, until you bring them back with using Base::name; . Always write override or @Override : if the signature does not actually match, the compiler tells you instead of silently creating a new method.

### super and the order of construction

A child object contains its parent's part, so the parent's part has to be built first. Constructors run from the top of the hierarchy down ; in C++, destructors run in exactly the reverse order, child first.

- Java : the first thing every constructor does is call a parent constructor. If you do not write super(...) , the compiler inserts super() — which fails to compile if the parent has no no-argument constructor. Until Java 24 the call had to be the very first statement; Java 25 allows statements that do not use the object before it.
- C++ : base classes are initialised in the member initialiser list ( Car(...) : Vehicle(4) ), before the derived class's own members and constructor body.
- Python : nothing is automatic. If a subclass defines __init__ and does not call super().__init__(...) , the parent's initialisation simply never runs and its attributes do not exist.

The program below builds a three-level chain and calls describe() through a parent-type reference; each override calls the parent's version before adding its own line.

```
#
include
<iostream>
#
include
<string>
using
namespace
std
;
class
Vehicle
{
protected
:
int
wheels
;
public
:
Vehicle
(
int
wheels
)
:
wheels
(
wheels
)
{
cout
<<
"Vehicle constructor\n"
;
}
virtual
~
Vehicle
(
)
=
default
;
virtual
void
describe
(
)
const
{
cout
<<
"Vehicle: "
<<
wheels
<<
" wheels\n"
;
}
}
;
class
Car
:
public
Vehicle
{
protected
:
string model
;
public
:
Car
(
string model
)
:
Vehicle
(
4
)
,
model
(
model
)
{
cout
<<
"Car constructor\n"
;
}
void
describe
(
)
const
override
{
Vehicle
::
describe
(
)
;
// C++ names the base class instead of super
cout
<<
"Car: "
<<
model
<<
"\n"
;
}
}
;
class
ElectricCar
:
public
Car
{
int
batteryKwh
;
public
:
ElectricCar
(
string model
,
int
kwh
)
:
Car
(
model
)
,
batteryKwh
(
kwh
)
{
cout
<<
"ElectricCar constructor\n"
;
}
void
describe
(
)
const
override
{
Car
::
describe
(
)
;
cout
<<
"ElectricCar: "
<<
batteryKwh
<<
" kWh battery\n"
;
}
}
;
int
main
(
)
{
ElectricCar
ev
(
"Nexon"
,
30
)
;
const
Vehicle
&
v
=
ev
;
// a parent-type reference to a child object
v
.
describe
(
)
;
// still runs ElectricCar::describe
return
0
;
}
```

Output

```
Vehicle constructor
Car constructor
ElectricCar constructor
Vehicle: 4 wheels
Car: Nexon
ElectricCar: 30 kWh battery
```

new calls ElectricCar's constructor, but its first act is super(model), whose first act is super(4): the calls climb ElectricCar → Car → Vehicle before any body runs.

- new calls ElectricCar's constructor, but its first act is super(model), whose first act is super(4): the calls climb ElectricCar → Car → Vehicle before any body runs.
- The topmost constructor's body runs first: Vehicle sets wheels = 4. The parent's part of the object must exist before a child can build on it.
- Back down one level, Car's body runs and sets model = "Nexon".
- Back down one level, ElectricCar's body runs and sets batteryKwh = 30. The object is complete only now, and bodies ran top-down.
- v is declared as a Vehicle, yet v.describe() looks the method up from the object's own class, ElectricCar, and finds ElectricCar's version there before Vehicle's is ever considered.
- Each describe() calls super.describe() before printing, so the calls climb to Vehicle and the lines come out top-down: Vehicle, Car, ElectricCar.

In the C++ version, when ev goes out of scope the destructors would run as ~ElectricCar , ~Car , ~Vehicle . The virtual destructor in Vehicle matters whenever a child is deleted through a parent pointer: without it, only ~Vehicle would run and the behaviour is undefined.

### The diamond problem

Suppose Scanner and Printer both inherit from Device , and Copier inherits from both. A Copier now reaches Device along two paths. Two questions follow: does a Copier hold one Device part or two (one per path)? And if Scanner and Printer both override a method, which one does Copier get? Each language answers differently.

### C++: virtual inheritance

Declaring the shared base virtual makes all paths share one subobject. The rule that surprises people: a virtual base is constructed first , and by the most derived class.

Copier inherits from Scanner and Printer, and both inherit from Device, so there are 2 paths from Copier up to Device: Copier → Scanner → Device and Copier → Printer → Device.

- Copier inherits from Scanner and Printer, and both inherit from Device, so there are 2 paths from Copier up to Device: Copier → Scanner → Device and Copier → Printer → Device.
- Without virtual, each path brings its own Device: the Scanner part holds one (id 1) and the Printer part another (id 2). Writing c.id is a compile error, because the compiler cannot tell which one you mean.
- With virtual inheritance the two paths share one Device, built first and by the most derived class: Copier's Device(3) runs and Scanner's Device(1) and Printer's Device(2) are skipped. Order: Device(3), Scanner, Printer, Copier.

```
#
include
<iostream>
using
namespace
std
;
struct
Device
{
int
id
;
Device
(
int
id
)
:
id
(
id
)
{
cout
<<
"Device("
<<
id
<<
")\n"
;
}
}
;
struct
Scanner
:
virtual
Device
{
// virtual: share one Device with siblings
Scanner
(
)
:
Device
(
1
)
{
cout
<<
"Scanner\n"
;
}
}
;
struct
Printer
:
virtual
Device
{
Printer
(
)
:
Device
(
2
)
{
cout
<<
"Printer\n"
;
}
}
;
struct
Copier
:
Scanner
,
Printer
{
Copier
(
)
:
Device
(
3
)
{
cout
<<
"Copier\n"
;
}
// the most derived class builds the shared base
}
;
int
main
(
)
{
Copier c
;
cout
<<
"one Device, id "
<<
c
.
id
<<
"\n"
;
// unambiguous: a single Device subobject
return
0
;
}
```

Output

```
Device(3)
Scanner
Printer
Copier
one Device, id 3
```

If Scanner and Printer both overrode a virtual function and Copier did not, the call would be ambiguous and the program would not compile; Copier must override it and decide.

### Java: interfaces and default methods

Java side-steps the data half of the problem: a class has exactly one superclass, and interfaces have no instance fields, so there is never a second copy of anything. Since Java 8, interfaces can carry default method bodies, which brings back the behaviour half. The rules: a method from a class wins over an interface default; a more specific interface wins over the one it extends; otherwise the class must override the method, and can call a particular parent with Interface.super.method() .

```
interface
Scanner
{
default
String
start
(
)
{
return
"Scanner ready"
;
}
}
interface
Printer
{
default
String
start
(
)
{
return
"Printer ready"
;
}
}
class
Copier
implements
Scanner
,
Printer
{
// Two defaults with the same signature: without this override, Copier does not compile.
@Override
public
String
start
(
)
{
return
Scanner
.
super
.
start
(
)
+
", "
+
Printer
.
super
.
start
(
)
;
}
}
public
class
Main
{
public
static
void
main
(
String
[
]
args
)
{
System
.
out
.
println
(
new
Copier
(
)
.
start
(
)
)
;
}
}
```

Output

```
Scanner ready, Printer ready
```

### Python: the method resolution order

Python builds one linear order of classes for every class — the method resolution order (MRO) , computed by the C3 linearisation algorithm — and looks attributes up along it. C3 guarantees that a class comes before its parents and that parents keep the order you listed them in; if no such order exists, the class definition fails with a TypeError . super() does not mean "my parent" — it means "the next class in the MRO of the object I was called on".

```
class
Device
:
def
__init__
(
self
)
:
print
(
"Device init"
)
def
start
(
self
)
:
return
"Device"
class
Scanner
(
Device
)
:
def
__init__
(
self
)
:
print
(
"Scanner init"
)
super
(
)
.
__init__
(
)
# in a Copier, the next class in the MRO is Printer
def
start
(
self
)
:
return
"Scanner -> "
+
super
(
)
.
start
(
)
class
Printer
(
Device
)
:
def
__init__
(
self
)
:
print
(
"Printer init"
)
super
(
)
.
__init__
(
)
def
start
(
self
)
:
return
"Printer -> "
+
super
(
)
.
start
(
)
class
Copier
(
Scanner
,
Printer
)
:
def
__init__
(
self
)
:
print
(
"Copier init"
)
super
(
)
.
__init__
(
)
print
(
[
cls
.
__name__
for
cls
in
Copier
.
__mro__
]
)
print
(
Copier
(
)
.
start
(
)
)
```

Output

```
['Copier', 'Scanner', 'Printer', 'Device', 'object']
Copier init
Scanner init
Printer init
Device init
Scanner -> Printer -> Device
```

C3 starts the order with Copier itself, then merges its parents' own orders and the list of its parents, Scanner before Printer, as written in the class statement.

- C3 starts the order with Copier itself, then merges its parents' own orders and the list of its parents, Scanner before Printer, as written in the class statement.
- Scanner heads its lists and appears in no list's tail, so it is taken and removed everywhere.
- Device is a head but still sits in the tail of another list, so it must wait; the next head, Printer, appears in no tail and is taken.
- Device heads its lists and appears in no list's tail, so it is taken and removed everywhere.
- object heads its lists and appears in no list's tail, so it is taken and removed everywhere.
- The MRO is Copier, Scanner, Printer, Device, object. super() means the next class in this list, so Scanner's super() reaches Printer, not Device: each initialiser runs once and start() returns "Scanner -> Printer -> Device".

This pattern is called cooperative multiple inheritance : it works only if every class in the chain calls super() . One class that calls Device.__init__(self) directly instead would break the chain.

### When to use inheritance

Inheritance couples a child tightly to its parent's implementation: a change to the parent can silently break children (the fragile base class problem ), and deep hierarchies are hard to follow. Use it when the is-a relationship is real and the child can stand in for the parent everywhere — the Liskov Substitution Principle . When you only want to reuse code, give the class a field holding the other object instead.

### Common mistakes

- Forgetting super().__init__(...) in a Python subclass, so the parent's attributes never exist.
- Changing an overriding method's parameters by accident and creating a new method; @Override and override catch this.
- Saying Java has no multiple inheritance at all — it has multiple inheritance of interfaces (types), just not of classes.
- Leaving out the virtual destructor in a C++ base class that is deleted through base pointers.
- Assuming Python's super() always means the direct parent; it follows the MRO of the actual object.
- Using inheritance just to reuse a few methods when the is-a test fails.

### Interview questions

In what order are constructors and destructors called in multilevel inheritance? Constructors run from the base downwards: Vehicle , then Car , then ElectricCar . In C++, destructors run in exactly the reverse order. With virtual inheritance, virtual base classes are constructed before everything else, by the most derived class.

Are constructors inherited? Not in Java: each class declares its own, and they call the parent's with super(...) . In C++ they are not inherited by default, but using Base::Base; opts in. In Python, __init__ is an ordinary method found through the MRO, so a subclass without its own __init__ uses its parent's.

What happens in Java if the parent class has no no-argument constructor? Every subclass constructor must then call one of the parent's constructors explicitly with super(arguments) . If it does not, the compiler inserts super() , finds no matching constructor and reports an error.

Can you override a private or a static method in Java? No. A private method is invisible to the subclass, so a method with the same name in the child is a new, unrelated method. A static method with the same signature hides the parent's: which one runs depends on the declared type of the reference, not the object.

What are public, protected and private inheritance in C++? They set the most open access that inherited members can have in the derived class. Public inheritance keeps the parent's access levels and models is-a. Protected inheritance turns public members into protected ones, and private inheritance turns them all private, which means "implemented in terms of" and stops outside code treating the child as the parent.

How does Python decide which method to call with multiple inheritance? It walks the class's method resolution order, ClassName.__mro__ , which C3 linearisation computes so that every class precedes its parents and the listed order of parents is kept. The first class in that order that defines the method wins. super() continues from the current class's position in that same order.

How does C++ virtual inheritance solve the diamond problem? Marking the shared base virtual in the intermediate classes makes them share a single base-class subobject instead of each carrying its own. Access to the base's members becomes unambiguous. The most derived class is responsible for constructing the virtual base.

Is multiple inheritance bad? Not in itself, but it adds complexity: diamonds, constructor ordering and name clashes. Java's designers kept it for interfaces only. In C++ and Python, inheriting from several small, stateless "interface-like" or mixin classes is common and safe; inheriting state from several concrete classes is where trouble starts.

Next, read Polymorphism , then check yourself with the OOP Intermediate skill test .

### What are the types of inheritance in OOP?

Single (one parent, one child), multilevel (a chain such as A to B to C), hierarchical (several children of one parent), multiple (one child with several parents) and hybrid (a combination, typically a diamond). C++ and Python support all five with classes; Java supports multiple and hybrid inheritance only through interfaces.

### Why does Java not support multiple inheritance of classes?

To avoid the ambiguity of the diamond problem: if two parent classes both had a field or method with the same name, which one would the child get? Java keeps one superclass per class and lets a class implement many interfaces, which carry no instance state, so only method clashes remain and the compiler makes you resolve them.

### What is the diamond problem?

It arises when class D inherits from B and C, which both inherit from A. D then has two paths to A, so it is unclear whether D holds one copy of A's data or two, and which version of an overridden method it should use. C++ solves it with virtual inheritance, Python with its method resolution order.

### What is the difference between method overriding and method hiding?

Overriding replaces an inherited instance method, and the version that runs is chosen at run time from the object's actual class. Hiding happens with static methods in Java, or with non-virtual functions in C++: the version is chosen at compile time from the variable's declared type, so a parent-typed reference still calls the parent's version.

### What does the super keyword do?

It refers to the parent class's version of something from inside a subclass. super(...) in Java, or super().__init__(...) in Python, calls the parent constructor; super.method() or super().method() calls the parent's version of an overridden method. C++ has no super keyword and names the base class explicitly, as in Base::method().


---

## Module 6: Polymorphism

*Original URL: https://codekairo.com/notes/oop/polymorphism*

### Overview

Quick answer

### What is polymorphism in OOP?

Polymorphism means one interface with many implementations: the same call does different things depending on the types involved. Compile-time polymorphism is method and operator overloading, resolved by the compiler from argument types. Run-time polymorphism is method overriding, where the object's actual class decides which method runs through dynamic dispatch — virtual functions and a vtable in C++.

- What polymorphism means
- Compile-time polymorphism
- Run-time polymorphism
- Overloading vs overriding
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Polymorphism — Greek for "many forms" — is the ability of one interface to work with many types. A single call, employee.pay() , does the right thing for a manager, an engineer and an intern; a single operator, + , adds numbers, joins strings and adds vectors. It is the pillar that lets you add a new class without editing the code that uses it. This note separates the two kinds interviewers ask about — compile-time and run-time — explains how a virtual call actually works (the vtable), and covers upcasting, downcasting and C++'s object slicing.

### What polymorphism means

There are two moments at which a program can decide which code a call runs:

- Compile time (static or early binding) — the compiler picks the function from the declared types of the arguments. This is overloading : several functions share a name but have different parameter lists, and operator overloading.
- Run time (dynamic or late binding) — the program picks the method while it runs, from the actual class of the object. This is overriding with dynamic dispatch .

area(5) has 1 int argument, so only int area(int side) fits and the other overload is rejected for its parameter count. The choice is fixed in the compiled code; it returns 25.

- area(5) has 1 int argument, so only int area(int side) fits and the other overload is rejected for its parameter count. The choice is fixed in the compiled code; it returns 25.
- area(3, 4) has 2 int arguments, so only int area(int width, int height) fits and the other overload is rejected for its parameter count. The choice is fixed in the compiled code; it returns 12.
- For e->pay() the compiler sees only Employee*, so it can only emit "call whatever is in slot pay". The one call site then runs Manager::pay, Engineer::pay, Intern::pay in turn, chosen by each object.

Type theory names a third kind, parametric polymorphism : one generic piece of code that works for any type, such as List<T> in Java or vector<T> in C++. C++ templates are compiled into a separate version per type; Java generics are compiled once and the type parameters are erased.

### Method overloading

Two methods overload each other when they share a name and differ in the number, types or order of their parameters. The compiler picks the best match for each call.

- A difference in return type alone is not enough: int area(int) and long area(int) cannot coexist, because the call area(5) gives the compiler nothing to choose by.
- Java resolves overloads in phases: first without boxing or varargs (but with widening such as int to long ), then with boxing, then with varargs. So with f(long) and f(Integer) both present, f(5) calls f(long) .
- C++ reports an error when two candidates match equally well — an ambiguous call .
- Python and JavaScript have no overloading. A second def area(...) replaces the first. Use default arguments, *args , or functools.singledispatch , which dispatches on the first argument's type at run time.

### Operator overloading

Operator overloading gives an operator a meaning for your own class. C++ defines operator+ , operator== and so on as functions; Python maps operators to special methods ( + calls __add__ , == calls __eq__ , len() calls __len__ ). Java and JavaScript do not allow it, so their classes use named methods such as plus .

```
#
include
<iostream>
using
namespace
std
;
int
area
(
int
side
)
{
return
side
*
side
;
}
// two overloads: the compiler
int
area
(
int
width
,
int
height
)
{
return
width
*
height
;
}
// picks one per call
struct
Vec2
{
int
x
,
y
;
Vec2
operator
+
(
const
Vec2
&
o
)
const
{
return
{
x
+
o
.
x
,
y
+
o
.
y
}
;
}
// operator overloading
}
;
ostream
&
operator
<<
(
ostream
&
out
,
const
Vec2
&
v
)
{
// lets cout print a Vec2
return
out
<<
"("
<<
v
.
x
<<
", "
<<
v
.
y
<<
")"
;
}
int
main
(
)
{
cout
<<
"square area: "
<<
area
(
5
)
<<
"\n"
;
cout
<<
"rectangle area: "
<<
area
(
3
,
4
)
<<
"\n"
;
Vec2 a
{
1
,
2
}
,
b
{
3
,
4
}
;
cout
<<
a
<<
" + "
<<
b
<<
" = "
<<
a
+
b
<<
"\n"
;
return
0
;
}
```

Output

```
square area: 25
rectangle area: 12
(1, 2) + (3, 4) = (4, 6)
```

### Overriding and dynamic dispatch

A subclass overrides an inherited method by defining one with the same signature. When code calls that method through a reference of the parent type, the program looks at the object's real class and runs that class's version. This is dynamic dispatch , and it is what lets payroll(employees) handle a class that did not exist when payroll was written.

Which methods dispatch dynamically differs by language:

- C++ — only functions declared virtual in the base class. A non-virtual function is bound at compile time to the declared type.
- Java — every instance method that is not static , private or final . (A final method cannot be overridden, so there is nothing to choose between.)
- Python and JavaScript — every method; the name is looked up on the object's class each time it is called.

The program below keeps a list of Employee references holding three different classes. The loop never asks what each one is — each object's own pay() runs. At the end it downcasts to find the managers, the only ones with an approveLeave method.

```
#
include
<iostream>
#
include
<memory>
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
class
Employee
{
protected
:
string name
;
public
:
Employee
(
string n
)
:
name
(
n
)
{
}
virtual
~
Employee
(
)
=
default
;
virtual
string
role
(
)
const
=
0
;
virtual
int
pay
(
)
const
=
0
;
// dispatched at run time
void
describe
(
)
const
{
cout
<<
name
<<
" ("
<<
role
(
)
<<
"): "
<<
pay
(
)
<<
"\n"
;
}
}
;
class
Manager
:
public
Employee
{
int
salary
,
bonus
;
public
:
Manager
(
string n
,
int
s
,
int
b
)
:
Employee
(
n
)
,
salary
(
s
)
,
bonus
(
b
)
{
}
string
role
(
)
const
override
{
return
"Manager"
;
}
int
pay
(
)
const
override
{
return
salary
+
bonus
;
}
void
approveLeave
(
)
const
{
cout
<<
name
<<
" approves leave\n"
;
}
}
;
class
Engineer
:
public
Employee
{
int
salary
;
public
:
Engineer
(
string n
,
int
s
)
:
Employee
(
n
)
,
salary
(
s
)
{
}
string
role
(
)
const
override
{
return
"Engineer"
;
}
int
pay
(
)
const
override
{
return
salary
;
}
}
;
class
Intern
:
public
Employee
{
int
stipend
;
public
:
Intern
(
string n
,
int
s
)
:
Employee
(
n
)
,
stipend
(
s
)
{
}
string
role
(
)
const
override
{
return
"Intern"
;
}
int
pay
(
)
const
override
{
return
stipend
;
}
}
;
int
main
(
)
{
vector
<
unique_ptr
<
Employee
>>
staff
;
staff
.
push_back
(
make_unique
<
Manager
>
(
"Meera"
,
120000
,
30000
)
)
;
staff
.
push_back
(
make_unique
<
Engineer
>
(
"Arjun"
,
90000
)
)
;
staff
.
push_back
(
make_unique
<
Intern
>
(
"Riya"
,
25000
)
)
;
int
total
=
0
;
for
(
const
auto
&
e
:
staff
)
{
// upcast: every element is used as an Employee
e
->
describe
(
)
;
total
+=
e
->
pay
(
)
;
}
cout
<<
"Payroll total: "
<<
total
<<
"\n"
;
for
(
const
auto
&
e
:
staff
)
// checked downcast: nullptr unless e really is a Manager
if
(
auto
m
=
dynamic_cast
<
const
Manager
*
>
(
e
.
get
(
)
)
)
m
->
approveLeave
(
)
;
return
0
;
}
```

Output

```
Meera (Manager): 150000
Arjun (Engineer): 90000
Riya (Intern): 25000
Payroll total: 265000
Meera approves leave
```

Notice describe() in the base class: it calls role() and pay() , and those calls dispatch to the subclass even though describe itself was written in Employee . A base class can therefore define the outline of an algorithm and leave steps to subclasses — the Template Method pattern.

### How a virtual call works: the vtable

C++ compilers implement virtual functions with a virtual table (vtable) : one array of function pointers per class, one slot per virtual function, which every object reaches through a hidden pointer, the vptr , set by its constructor. The standard does not require it, but GCC, Clang and MSVC all work this way:

Every object of a class with virtual functions carries a hidden vptr, set by its constructor, pointing at its class's vtable. Each class's table has the same slots in the same order; an override fills its slot with that class's own function.

- Every object of a class with virtual functions carries a hidden vptr, set by its constructor, pointing at its class's vtable. Each class's table has the same slots in the same order; an override fills its slot with that class's own function.
- e->pay() for staff[0] compiles to: follow e's vptr, read the third slot (pay), call what is there. Here that is Manager::pay, which returns 120000 + 30000 = 150000.
- The same machine code for staff[1] reads a different vptr and so a different table, and runs Engineer::pay: 90000.
- The same machine code for staff[2] reads a different vptr and so a different table, and runs Intern::pay: 25000. The loop never asked which class it held; the total is 265000.

The cost is one pointer per object, one table per class and an indirect call that the compiler usually cannot inline — negligible in most code, noticeable in very tight loops. Java's JVM uses the same idea (method tables), and its JIT compiler often removes the indirection when it can prove only one class is ever seen at a call site. Python looks the method name up on the object's class at each call, through the MRO.

### Upcasting and downcasting

Upcasting is treating a child object as its parent type: putting a Manager into a list of Employee . It is always safe and implicit, because every manager is an employee. Downcasting goes the other way — treating an Employee reference as a Manager — and is safe only if the object really is a manager, so it must be checked.

Upcasting: each element is used through an Employee pointer, whatever its real class. That is always safe, because every Manager, Engineer and Intern is an Employee.

- Upcasting: each element is used through an Employee pointer, whatever its real class. That is always safe, because every Manager, Engineer and Intern is an Employee.
- dynamic_cast checks the object's real class at run time: Meera is a Manager, so the cast returns a usable Manager pointer and approveLeave() can be called.
- Arjun is an Engineer, which is not a Manager anywhere up its chain (Engineer → Employee), so the cast returns nullptr instead of a pointer to the wrong thing.
- Riya is an Intern, which is not a Manager anywhere up its chain (Intern → Employee), so the cast returns nullptr instead of a pointer to the wrong thing.

A chain of downcasts ( if it is a Manager... else if it is an Intern... ) is usually a sign that the behaviour belongs in an overridden method instead.

### Object slicing in C++

Polymorphism in C++ works only through pointers and references . If you copy a derived object into a base-class value , only the base part is copied — the derived part is sliced off — and the copy really is a base object, so its virtual calls run the base versions:

```
#
include
<iostream>
#
include
<string>
using
namespace
std
;
class
Employee
{
public
:
virtual
~
Employee
(
)
=
default
;
virtual
string
role
(
)
const
{
return
"Employee"
;
}
}
;
class
Manager
:
public
Employee
{
public
:
string
role
(
)
const
override
{
return
"Manager"
;
}
}
;
void
byValue
(
Employee e
)
{
cout
<<
"by value: "
<<
e
.
role
(
)
<<
"\n"
;
}
// copies only the Employee part
void
byReference
(
const
Employee
&
e
)
{
cout
<<
"by reference: "
<<
e
.
role
(
)
<<
"\n"
;
}
int
main
(
)
{
Manager m
;
byValue
(
m
)
;
byReference
(
m
)
;
Employee copy
=
m
;
// sliced as well
cout
<<
"assigned copy: "
<<
copy
.
role
(
)
<<
"\n"
;
return
0
;
}
```

Output

```
by value: Employee
by reference: Manager
assigned copy: Employee
```

Passing m by value copies only the Employee part into a new Employee object, whose constructor points its vptr at Employee's vtable. The Manager part is cut away, so role() answers "Employee". Employee copy = m slices the same way.

- Passing m by value copies only the Employee part into a new Employee object, whose constructor points its vptr at Employee's vtable. The Manager part is cut away, so role() answers "Employee". Employee copy = m slices the same way.
- By reference nothing is copied: e is another name for m itself, the vptr still points at Manager's vtable, and role() answers "Manager". Polymorphism in C++ needs a pointer or a reference.

Java and Python cannot slice, because their variables only ever hold references.

### Common mistakes

- Trying to overload on return type alone; the compiler rejects it.
- Forgetting virtual in C++ and wondering why the base version runs through a base pointer.
- Passing a C++ derived object to a function that takes the base by value , slicing it.
- Writing two def methods with the same name in Python and expecting overloading.
- Calling an overridable method from a Java constructor; it runs the subclass version before the subclass's fields are initialised.
- Using static_cast for a downcast whose type you have not checked.

### Interview questions

Can a method be overloaded on return type only? No, in C++ and Java. A call such as area(5) must be resolvable from its arguments, and the return type does not appear at the call site — it may even be discarded. Java reports the second method as "already defined"; C++ reports that the functions cannot be overloaded.

Can a constructor be virtual in C++? No. A virtual call needs the object's vptr, which the constructor itself sets up; and when you construct an object you already name its exact type. To create a copy of an object whose type you do not know, give the base class a virtual clone() method. Destructors, on the other hand, should be virtual in any base class used polymorphically.

What happens if a constructor calls a virtual method? In C++ the call dispatches to the class whose constructor is running, not the most derived class, because the derived part does not exist yet. In Java and Python the most derived override runs — before the subclass's own constructor has initialised its fields, so it sees default values such as null or 0 . Both are reasons to avoid calling overridable methods from constructors.

What is the difference between early binding and late binding? Early (static) binding fixes which function a call runs at compile time — overloads, non-virtual C++ functions, and Java's static, private and final methods. Late (dynamic) binding chooses at run time from the object's actual class — virtual functions in C++, ordinary instance methods in Java, every method in Python.

What is the difference between static_cast and dynamic_cast? static_cast converts at compile time with no run-time check, so a wrong downcast is undefined behaviour. dynamic_cast checks the object's real type at run time using its type information, returning nullptr for a failed pointer cast or throwing std::bad_cast for a failed reference cast, and it requires the base class to have at least one virtual function.

How does Python achieve polymorphism without overloading or declared types? Through duck typing: any object with the right method can be used, whatever its class, so a function that calls obj.pay() works for anything with a pay method. Overloading-like behaviour comes from default arguments, *args , and functools.singledispatch .

Are generics and templates a form of polymorphism? Yes, parametric polymorphism: one definition works for many types. C++ templates generate a separate compiled version for each type used. Java generics are checked at compile time and then erased, so one compiled class serves every type argument and the type is not available at run time.

Can you achieve run-time polymorphism with data members? No. Fields are not overridden: in Java, a subclass field with the same name hides the parent's, and which one you read depends on the reference's declared type. Only methods dispatch dynamically, which is one more reason to keep fields private and expose behaviour through methods.

Next, read Abstraction: Abstract Classes and Interfaces , then check yourself with the OOP Intermediate skill test .

### What are the types of polymorphism in OOP?

Interviews usually expect two: compile-time (static) polymorphism, which is method and operator overloading, and run-time (dynamic) polymorphism, which is method overriding with dynamic dispatch. Type theory adds parametric polymorphism, which is generics in Java and templates in C++, where one piece of code works for many types.

### What is the difference between method overloading and method overriding?

Overloading is several methods with the same name but different parameter lists, usually in one class, chosen by the compiler from the argument types. Overriding is a subclass redefining an inherited method with the same signature, chosen at run time from the object's actual class. Overloading needs no inheritance; overriding does.

### Does Python support method overloading?

Not by signature. Defining a second method with the same name simply replaces the first. Python gets the same effect with default argument values, *args and **kwargs, or functools.singledispatch, which picks an implementation from the type of the first argument at run time.

### What is a virtual function in C++?

A virtual function is a member function declared with the virtual keyword in a base class so that a call through a base pointer or reference runs the derived class's override. Without virtual, the call is bound at compile time to the version in the pointer's declared type.

### Does Java support operator overloading?

No. Java does not let programmers define operators for their own classes. The one built-in exception is + on String, which the compiler turns into string concatenation. Classes like BigInteger and BigDecimal therefore offer methods such as add and multiply instead of operators.


---

## Module 7: SOLID Principles

*Original URL: https://codekairo.com/notes/oop/solid-principles*

### Overview

Quick answer

### What are the SOLID principles in OOP?

SOLID is a set of five object-oriented design principles collected by Robert C. Martin: Single Responsibility (a class has one reason to change), Open/Closed (extend behaviour without editing tested code), Liskov Substitution (a subtype must work wherever its base type does), Interface Segregation (small, focused interfaces) and Dependency Inversion (depend on abstractions, not concrete classes).

- S: Single Responsibility Principle
- O: Open/Closed Principle
- L: Liskov Substitution Principle
- I: Interface Segregation Principle
- D: Dependency Inversion Principle
- Spotting violations
- Common mistakes
- Interview questions
- Common questions
- Test yourself

SOLID is an acronym for five principles of object-oriented design. They are not rules a compiler checks; they are tests you apply to a design to predict whether it will be easy or painful to change. Each one names a specific kind of pain — one class edited for unrelated reasons, a switch that grows with every feature, a subclass that breaks callers, an interface nobody can fully implement, business logic welded to a database — and the fix for it. This note takes each principle in turn with a violation, a fix and, for the code-shaped ones, a program.

### S: Single Responsibility Principle

A class should have only one reason to change.

Robert C. Martin later sharpened "reason to change" to actor : a class should be responsible to one group of people who might ask for changes.

Violation. An Invoice class that computes the total with taxes, formats the invoice as a PDF, and saves it to the database. Three different people ask for changes to it: the finance team (tax rules), the design team (layout) and the database administrator (schema). A layout change risks breaking tax calculation, because both live in one class and share its fields.

Fix. Split by actor: InvoiceCalculator for totals, InvoicePdfRenderer for layout, InvoiceRepository for storage, with Invoice left as the data the three work on.

Before: one Invoice class computes taxes, lays out the PDF and stores itself. Three groups of people ask for changes to it, so a layout change can break the tax code it shares fields with.

- Before: one Invoice class computes taxes, lays out the PDF and stores itself. Three groups of people ask for changes to it, so a layout change can break the tax code it shares fields with.
- After: one class per actor. Each has a single reason to change, and Invoice is just the data the three work on, so the design team can no longer break a tax calculation.

SRP does not mean "one method per class". A Stack with push , pop and peek has one responsibility. The smell to look for is a class whose methods fall into groups that use different fields and change for different reasons.

### O: Open/Closed Principle

Software entities should be open for extension, but closed for modification.

Bertrand Meyer stated it in 1988 with inheritance in mind; today it is usually read through polymorphism: depend on an abstraction, and add behaviour by adding a new implementation of it.

Violation. A checkout function that switches on the customer type, so every new offer means editing, re-testing and re-deploying it. Fix. Make the discount an abstraction; each offer is its own class, and checkout is never edited again:

Before: checkout switches on a type code. Adding the Festive offer means editing a function that already works and is tested, and re-testing every branch in it.

- Before: checkout switches on a type code. Adding the Festive offer means editing a function that already works and is tested, and re-testing every branch in it.
- After: checkout depends only on the DiscountPolicy abstraction. FestiveDiscount arrives as a new class, checkout is untouched, and the three pay 1000, 900, 750 exactly as the switch computed.

In the program, FestiveDiscount was "added later" without touching checkout :

```
#
include
<algorithm>
#
include
<iostream>
#
include
<memory>
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
class
DiscountPolicy
{
// the abstraction checkout depends on
public
:
virtual
~
DiscountPolicy
(
)
=
default
;
virtual
string
name
(
)
const
=
0
;
virtual
int
apply
(
int
amount
)
const
=
0
;
}
;
class
NoDiscount
:
public
DiscountPolicy
{
public
:
string
name
(
)
const
override
{
return
"Regular"
;
}
int
apply
(
int
amount
)
const
override
{
return
amount
;
}
}
;
class
StudentDiscount
:
public
DiscountPolicy
{
public
:
string
name
(
)
const
override
{
return
"Student"
;
}
int
apply
(
int
amount
)
const
override
{
return
amount
*
90
/
100
;
}
}
;
class
FestiveDiscount
:
public
DiscountPolicy
{
// added later: checkout() did not change
public
:
string
name
(
)
const
override
{
return
"Festive"
;
}
int
apply
(
int
amount
)
const
override
{
return
amount
-
min
(
amount
/
4
,
500
)
;
}
}
;
int
checkout
(
int
amount
,
const
DiscountPolicy
&
policy
)
{
return
policy
.
apply
(
amount
)
;
}
// closed
int
main
(
)
{
vector
<
unique_ptr
<
DiscountPolicy
>>
policies
;
policies
.
push_back
(
make_unique
<
NoDiscount
>
(
)
)
;
policies
.
push_back
(
make_unique
<
StudentDiscount
>
(
)
)
;
policies
.
push_back
(
make_unique
<
FestiveDiscount
>
(
)
)
;
for
(
const
auto
&
p
:
policies
)
cout
<<
p
->
name
(
)
<<
" customer pays "
<<
checkout
(
1000
,
*
p
)
<<
"\n"
;
return
0
;
}
```

Output

```
Regular customer pays 1000
Student customer pays 900
Festive customer pays 750
```

Somewhere a factory still has to pick which policy to create, so one place in the program does change. The principle is about keeping that place small and keeping the tested business logic out of it. This structure is the Strategy pattern, covered in Design Patterns for Interviews .

### L: Liskov Substitution Principle

If S is a subtype of T, objects of type T may be replaced with objects of type S without breaking the program.

The principle comes from Barbara Liskov, and the precise version (with Jeannette Wing, 1994) is about behaviour , not method signatures. A subtype must:

- accept at least what the base accepts — preconditions cannot be strengthened ;
- deliver at least what the base promises — postconditions cannot be weakened ;
- keep the base's invariants , and not throw exceptions the base's callers do not expect.

Violation. The classic example: Square extends Rectangle . Mathematically a square is a rectangle. But a mutable Rectangle promises that setWidth leaves the height alone, and a Square cannot keep that promise:

```
#
include
<iostream>
#
include
<string>
using
namespace
std
;
class
Rectangle
{
protected
:
int
w
=
0
,
h
=
0
;
public
:
virtual
~
Rectangle
(
)
=
default
;
virtual
void
setWidth
(
int
x
)
{
w
=
x
;
}
virtual
void
setHeight
(
int
x
)
{
h
=
x
;
}
int
area
(
)
const
{
return
w
*
h
;
}
}
;
class
Square
:
public
Rectangle
{
// keeps its sides equal, breaking Rectangle's promise
public
:
void
setWidth
(
int
x
)
override
{
w
=
h
=
x
;
}
void
setHeight
(
int
x
)
override
{
w
=
h
=
x
;
}
}
;
void
resize
(
Rectangle
&
r
,
const
string
&
label
)
{
// written for Rectangle
r
.
setWidth
(
5
)
;
r
.
setHeight
(
4
)
;
// relies on the width staying 5
cout
<<
label
<<
": expected 20, got "
<<
r
.
area
(
)
<<
"\n"
;
}
int
main
(
)
{
Rectangle r
;
Square s
;
resize
(
r
,
"Rectangle"
)
;
resize
(
s
,
"Square"
)
;
return
0
;
}
```

Output

```
Rectangle: expected 20, got 20
Square: expected 20, got 16
```

resize() is written against Rectangle's promise: setting the width leaves the height alone. Both shapes start at 0 by 0.

- resize() is written against Rectangle's promise: setting the width leaves the height alone. Both shapes start at 0 by 0.
- set_width(5): the rectangle is 5 wide and still 0 high, as promised. Square's override keeps its sides equal, so its height changed too: it is 5 by 5.
- set_height(4): the rectangle becomes 5 by 4. The square sets both sides again and becomes 4 by 4 — the width resize() relied on has changed under it.
- area() is 20 for the rectangle and 16 for the square. A subtype that breaks what callers of its base type rely on is not substitutable, whatever the maths says.

Fix. Do not model the relationship with mutable inheritance. Make shapes immutable (a Square that cannot be resized never breaks a promise about resizing), or make Rectangle and Square siblings under a Shape abstraction that only promises area() . The same shape of bug appears with Bird.fly() and a Penguin that throws: split out a FlyingBird type so only birds that fly promise to.

The practical test: if a subclass needs to throw "not supported", do nothing, or check its own type to honour an inherited method, it is probably not a true subtype.

### I: Interface Segregation Principle

Clients should not be forced to depend on methods they do not use.

Violation. One fat Machine interface with print , scan and fax . A basic printer must implement scan and fax by throwing exceptions — an LSP problem waiting to happen — and every client that only prints is recompiled and retested whenever the fax method changes.

Before: one Machine interface with print, scan and fax. BasicPrinter must implement all three and throw from 2 of them, and every client that only prints changes when the fax method does.

- Before: one Machine interface with print, scan and fax. BasicPrinter must implement all three and throw from 2 of them, and every client that only prints changes when the fax method does.
- After: Printer, Scanner and Fax. BasicPrinter implements only Printer, OfficeMachine all three, and printAll asks for a Printer — so no class implements a method it cannot honour.

Fix. Split the interface by what clients need. A device implements as many small interfaces as it supports, and each function asks for only the capability it uses:

```
interface
Printer
{
void
print
(
String
doc
)
;
}
interface
Scanner
{
String
scan
(
)
;
}
interface
Fax
{
void
fax
(
String
doc
,
String
number
)
;
}
class
BasicPrinter
implements
Printer
{
// implements only what it can do
public
void
print
(
String
doc
)
{
System
.
out
.
println
(
"BasicPrinter prints "
+
doc
)
;
}
}
class
OfficeMachine
implements
Printer
,
Scanner
,
Fax
{
public
void
print
(
String
doc
)
{
System
.
out
.
println
(
"OfficeMachine prints "
+
doc
)
;
}
public
String
scan
(
)
{
return
"scan-001.pdf"
;
}
public
void
fax
(
String
doc
,
String
number
)
{
System
.
out
.
println
(
"OfficeMachine faxes "
+
doc
+
" to "
+
number
)
;
}
}
public
class
Main
{
static
void
printAll
(
Printer
p
,
String
.
.
.
docs
)
{
// depends only on printing
for
(
String
d
:
docs
)
p
.
print
(
d
)
;
}
public
static
void
main
(
String
[
]
args
)
{
printAll
(
new
BasicPrinter
(
)
,
"notes.pdf"
)
;
OfficeMachine
office
=
new
OfficeMachine
(
)
;
printAll
(
office
,
"invoice.pdf"
)
;
office
.
fax
(
office
.
scan
(
)
,
"080-0000"
)
;
}
}
```

Output

```
BasicPrinter prints notes.pdf
OfficeMachine prints invoice.pdf
OfficeMachine faxes scan-001.pdf to 080-0000
```

ISP is SRP seen from the caller's side: an interface should have one reason to change, and that reason is the needs of its clients.

### D: Dependency Inversion Principle

High-level modules should not depend on low-level modules; both should depend on abstractions. Abstractions should not depend on details; details should depend on abstractions.

Violation. An OrderNotifier (business policy) that creates an EmailSender (a detail) inside itself. Switching to SMS means editing the notifier, and testing it sends real email.

Before: the business policy creates an EmailSender itself, so its only dependency arrow points down at a detail. Switching to SMS means editing OrderNotifier, and testing it sends real email.

- Before: the business policy creates an EmailSender itself, so its only dependency arrow points down at a detail. Switching to SMS means editing OrderNotifier, and testing it sends real email.
- After: OrderNotifier owns a MessageSender interface and receives a sender through its constructor. All 3 details now point up at that abstraction — the inversion — and the fake one records 1 message for a test instead of sending.

Fix. The high-level module defines the abstraction it needs — a MessageSender interface — and receives an implementation from outside, through its constructor. The arrows of dependency now point from the senders to the abstraction the policy owns; that reversal is the "inversion". A fake implementation makes the notifier testable without any network:

```
#
include
<iostream>
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
class
MessageSender
{
// the abstraction, owned by the high-level policy
public
:
virtual
~
MessageSender
(
)
=
default
;
virtual
void
send
(
const
string
&
to
,
const
string
&
text
)
=
0
;
}
;
class
EmailSender
:
public
MessageSender
{
public
:
void
send
(
const
string
&
to
,
const
string
&
text
)
override
{
cout
<<
"email to "
<<
to
<<
": "
<<
text
<<
"\n"
;
}
}
;
class
SmsSender
:
public
MessageSender
{
public
:
void
send
(
const
string
&
to
,
const
string
&
text
)
override
{
cout
<<
"sms to "
<<
to
<<
": "
<<
text
<<
"\n"
;
}
}
;
class
FakeSender
:
public
MessageSender
{
// for tests: records instead of sending
public
:
vector
<
string
>
sent
;
void
send
(
const
string
&
,
const
string
&
text
)
override
{
sent
.
push_back
(
text
)
;
}
}
;
class
OrderNotifier
{
// high-level: knows nothing about email or SMS
MessageSender
&
sender
;
public
:
explicit
OrderNotifier
(
MessageSender
&
s
)
:
sender
(
s
)
{
}
// constructor injection
void
shipped
(
int
orderId
,
const
string
&
to
)
{
sender
.
send
(
to
,
"Order "
+
to_string
(
orderId
)
+
" shipped"
)
;
}
}
;
int
main
(
)
{
EmailSender email
;
SmsSender sms
;
FakeSender fake
;
OrderNotifier
(
email
)
.
shipped
(
42
,
"asha@example.com"
)
;
OrderNotifier
(
sms
)
.
shipped
(
42
,
"90000 00001"
)
;
OrderNotifier
(
fake
)
.
shipped
(
7
,
"test"
)
;
cout
<<
"fake sender recorded "
<<
fake
.
sent
.
size
(
)
<<
" message: "
<<
fake
.
sent
[
0
]
<<
"\n"
;
return
0
;
}
```

Output

```
email to asha@example.com: Order 42 shipped
sms to 90000 00001: Order 42 shipped
fake sender recorded 1 message: Order 7 shipped
```

In Python the abstraction is implicit — duck typing means any object with send(to, text) will do — but the principle is the same: OrderNotifier never names a concrete sender.

Three terms are often mixed up:

### Common mistakes

- Reading SRP as "a class should do one thing" or "have one method"; it is about one reason, or actor, for change.
- Thinking OCP forbids ever editing a file; it is about not editing tested code to add a new variant.
- Judging LSP by method signatures alone; it is about behaviour and promises.
- Creating an interface for every class, each with one implementation, "for SOLID"; abstractions should earn their place.
- Confusing dependency inversion (a principle) with dependency injection (a technique) or with a DI framework.
- Applying all five everywhere in a small script; they pay off where code changes often.

### Interview questions

Explain the Single Responsibility Principle with an example. A class should have one reason to change. An Employee class that calculates pay (owned by finance), formats reports (owned by HR) and saves itself to a database (owned by the DBA) has three. Splitting it into a pay calculator, a report formatter and a repository means a change for one group cannot break the others.

How does the Strategy pattern relate to the Open/Closed Principle? Strategy puts each variant of an algorithm behind a common interface, and the code that uses it calls the interface only. Adding a variant means adding a class, not editing the user — which is exactly "open for extension, closed for modification".

Can Square ever safely extend Rectangle? Yes, if both are immutable. The LSP problem comes from Rectangle's promise that width and height change independently. If neither has setters and both only promise area() and their dimensions, a square satisfies every promise a rectangle makes.

Is there an LSP or ISP smell in the Java standard library? List.of(...) and Collections.unmodifiableList(...) return List objects whose add throws UnsupportedOperationException . The List contract documents add as an optional operation, so it is technically allowed, but callers holding a List cannot tell in advance which methods work — the kind of surprise ISP and LSP try to prevent.

What is the difference between dependency inversion and dependency injection? Dependency inversion is the principle that high-level policy should depend on abstractions rather than on low-level details. Dependency injection is one way to achieve it: the object receives its dependencies from the outside instead of constructing them. You can inject concrete classes and still violate the principle.

How do SRP and ISP differ? SRP is about the reasons a class changes; ISP is about what an interface forces on its clients. A class can have one responsibility yet expose a fat interface that different clients use different parts of — splitting that interface is ISP.

Can you overdo SOLID? Yes. Wrapping every class in an interface with a single implementation, or splitting code into dozens of one-method classes, adds indirection without making any likely change easier. Apply the principles where change actually happens, and prefer the simplest design that handles the changes you can foresee.

Which SOLID principle does a growing switch on object type violate? Mainly Open/Closed: every new type forces an edit to the switch, and to every other switch on the same type code. Moving the varying behaviour into a method on each type, so the switch becomes one polymorphic call, fixes it.

Next, read Design Patterns for Interviews , then check yourself with the OOP Intermediate skill test .

### Who created the SOLID principles?

Robert C. Martin gathered and described the five principles around 2000, and Michael Feathers later arranged them into the SOLID acronym. Two are older: the Open/Closed Principle comes from Bertrand Meyer's 1988 book on object-oriented software construction, and Liskov substitution from Barbara Liskov's work on data abstraction in the late 1980s.

### What is the difference between dependency inversion and dependency injection?

Dependency inversion is a design principle: high-level code should depend on abstractions, not on concrete low-level classes. Dependency injection is a technique that helps you follow it: an object receives its dependencies from outside, through its constructor, a setter or a parameter, instead of creating them itself.

### Why is Square extending Rectangle a violation of LSP?

Code written for a Rectangle may set the width and height independently and expect the area to be their product. A Square must keep its sides equal, so setting the height also changes the width, and that code breaks. The square is a rectangle mathematically, but a mutable Square is not substitutable for a mutable Rectangle.

### What does closed for modification mean in the Open/Closed Principle?

It means adding a new behaviour should not require editing code that already works and is tested. You extend the system by writing a new class that implements an existing abstraction, such as a new discount policy, and the code that uses the abstraction stays exactly as it was.

### Do the SOLID principles apply outside object-oriented programming?

Largely, yes. Single responsibility and interface segregation apply to modules, functions and services; dependency inversion is how hexagonal and clean architectures keep business logic independent of databases and frameworks. Liskov substitution applies to any system where one implementation is swapped for another behind a shared contract.


---

## Module 8: Design Patterns for Interviews

*Original URL: https://codekairo.com/notes/oop/design-patterns*

### Overview

Quick answer

### What are design patterns in object-oriented programming?

Design patterns are named, reusable solutions to problems that keep recurring in object-oriented design — making sure only one instance exists, notifying many objects of a change, swapping an algorithm at run time. The 1994 Gang of Four book catalogued 23 of them in three groups: creational, structural and behavioural. A pattern is a template for a design, not code to copy.

- What a design pattern is
- The three categories
- Singleton
- Factory
- Builder
- Adapter
- Decorator
- Observer
- Strategy
- The patterns at a glance
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A design pattern is a named, proven answer to a design problem that keeps coming up: "this object must exist only once", "many objects need to know when this one changes", "the algorithm should be swappable at run time". Knowing the patterns gives you two things in an interview: ready-made designs for low-level design rounds, and a vocabulary — saying "that is a Strategy" communicates a whole structure in one word. This note covers the three categories and then the seven patterns most often asked about, each with its intent, when to use it and its trade-offs, and runnable code for the most code-shaped ones.

### What a design pattern is

The patterns most people mean come from Design Patterns: Elements of Reusable Object-Oriented Software (1994) by Erich Gamma, Richard Helm, Ralph Johnson and John Vlissides — the Gang of Four (GoF) . The book describes each pattern by four elements: a name , the problem it addresses, the solution (a structure of classes and their responsibilities), and the consequences (the trade-offs).

Two cautions. A pattern is a design , not a library: you adapt it to your problem. And patterns depend on the language — Python's first-class functions turn Strategy into "pass a function", and every modern language builds Iterator into its for loop.

### Singleton

Intent. Ensure a class has exactly one instance and provide a global point of access to it.

When to use. For something that genuinely exists once per process: a configuration object, a logger, a connection pool. Structure: a private constructor, a static field holding the instance, and a static method returning it.

Thread safety is the follow-up every interviewer asks:

- C++11 and later : a function-local static is initialised exactly once even if several threads call the function at the same moment — the standard guarantees it. This "Meyers singleton" is the idiomatic form.
- Java : an eager static final field is safe because class initialisation is. For lazy creation, the holder idiom (a nested class whose static field is initialised on first use) is safe and lock-free. Double-checked locking works only if the field is volatile . A single-element enum is the form Effective Java recommends: it also resists creating a second instance through reflection or deserialisation.
- Python : a module is executed once and cached in sys.modules , so a module-level object is the idiomatic singleton. A class that overrides __new__ needs a lock if threads may race to create it.

Costs. A singleton is global state: it hides dependencies, couples classes to one implementation and makes tests share state. Prefer passing the single instance to the classes that need it.

```
#
include
<iostream>
#
include
<string>
using
namespace
std
;
class
Config
{
string logLevel
=
"INFO"
;
static
inline
int
created
=
0
;
// C++17 inline static member
Config
(
)
{
created
++
;
}
// private: nobody else can construct one
public
:
Config
(
const
Config
&
)
=
delete
;
// no copies
Config
&
operator
=
(
const
Config
&
)
=
delete
;
static
Config
&
instance
(
)
{
static
Config only
;
// initialised once, thread-safe since C++11
return
only
;
}
void
setLogLevel
(
const
string
&
level
)
{
logLevel
=
level
;
}
string
getLogLevel
(
)
const
{
return
logLevel
;
}
static
int
instancesCreated
(
)
{
return
created
;
}
}
;
int
main
(
)
{
Config
&
a
=
Config
::
instance
(
)
;
Config
&
b
=
Config
::
instance
(
)
;
a
.
setLogLevel
(
"DEBUG"
)
;
cout
<<
"same instance: "
<<
(
&
a
==
&
b
?
"yes"
:
"no"
)
<<
"\n"
;
cout
<<
"log level seen through b: "
<<
b
.
getLogLevel
(
)
<<
"\n"
;
cout
<<
"instances created: "
<<
Config
::
instancesCreated
(
)
<<
"\n"
;
return
0
;
}
```

Output

```
same instance: yes
log level seen through b: DEBUG
instances created: 1
```

Before the first call nothing exists: no Config object, and the nested Holder class has not even been loaded. The constructor is private, so instance() is the only way in.

- Before the first call nothing exists: no Config object, and the nested Holder class has not even been loaded. The constructor is private, so instance() is the only way in.
- The first instance() call loads Holder, whose static initialiser runs new Config() — created becomes 1 — and a receives that object.
- The second call finds Holder already initialised and returns the same object; created stays 1. No lock is needed: the JVM initialises a class once.
- a.setLogLevel("DEBUG") changes the one object, so b sees DEBUG too: a == b is true and exactly one instance was ever created.

### Factory

Intent. Separate deciding which class to create from using the object , so callers depend only on an interface.

Three things go by this name, and interviewers like you to tell them apart:

- Simple factory — a function or static method that picks a concrete class from a parameter: NotifierFactory.create("sms") returns an SmsNotifier typed as Notifier . Useful, but not one of the 23.
- Factory Method (GoF) — a base class declares a creation method and subclasses override it to choose the product. A Dialog calls createButton() ; WindowsDialog returns a WindowsButton , WebDialog an HtmlButton . The base class's logic never names a concrete button.
- Abstract Factory (GoF) — an object whose several methods create a whole family of related products that must match: a GuiFactory with createButton() and createCheckbox() , implemented once per platform.

When to use. When the concrete class depends on configuration or input, when creation involves more than a constructor call, or when you want new product types to be addable without touching the code that uses them (the Open/Closed Principle from SOLID Principles ).

### Builder

Intent. Construct a complex object step by step, separating the construction from the final representation.

When to use. When a class has many optional parameters. The alternative, telescoping constructors — Pizza(size) , Pizza(size, cheese) , Pizza(size, cheese, olives) and so on — is unreadable at the call site ( new Pizza("L", true, false, 2) : which true was cheese?). A builder names every step, can validate before building, and lets the finished object be immutable. Java's HttpRequest.newBuilder() and StringBuilder follow this style. Python and Kotlin rarely need it, because keyword arguments with defaults already name each value.

```
final
class
Pizza
{
// immutable once built
private
final
String
size
;
private
final
boolean
cheese
,
olives
;
private
final
int
extras
;
private
Pizza
(
Builder
b
)
{
size
=
b
.
size
;
cheese
=
b
.
cheese
;
olives
=
b
.
olives
;
extras
=
b
.
extras
;
}
@Override
public
String
toString
(
)
{
return
size
+
" pizza, cheese="
+
cheese
+
", olives="
+
olives
+
", extras="
+
extras
;
}
static
class
Builder
{
private
final
String
size
;
// required: taken by the builder's constructor
private
boolean
cheese
,
olives
;
private
int
extras
;
Builder
(
String
size
)
{
this
.
size
=
size
;
}
Builder
cheese
(
)
{
cheese
=
true
;
return
this
;
}
// each step returns the builder
Builder
olives
(
)
{
olives
=
true
;
return
this
;
}
Builder
extras
(
int
n
)
{
if
(
n
<
0
)
throw
new
IllegalArgumentException
(
"extras cannot be negative"
)
;
extras
=
n
;
return
this
;
}
Pizza
build
(
)
{
return
new
Pizza
(
this
)
;
}
}
}
public
class
Main
{
public
static
void
main
(
String
[
]
args
)
{
System
.
out
.
println
(
new
Pizza
.
Builder
(
"Large"
)
.
cheese
(
)
.
extras
(
2
)
.
build
(
)
)
;
System
.
out
.
println
(
new
Pizza
.
Builder
(
"Small"
)
.
olives
(
)
.
build
(
)
)
;
}
}
```

Output

```
Large pizza, cheese=true, olives=false, extras=2
Small pizza, cheese=false, olives=true, extras=0
```

The builder's constructor takes the one required value, the size. Every optional field starts at its default: no cheese, no olives, no extras.

- The builder's constructor takes the one required value, the size. Every optional field starts at its default: no cheese, no olives, no extras.
- cheese() sets one field and returns the builder itself, which is what lets the next call chain straight on.
- extras(2) checks its argument first — a negative count throws here, before any Pizza exists — then sets it and returns the builder again.
- build() copies the builder's fields into a new Pizza whose fields are final, so the finished object can never change. Its toString() prints the line in the note's output.

### Adapter

Intent. Convert the interface of an existing class into the interface the client expects, so classes with incompatible interfaces can work together.

When to use. When you must use a class you cannot change — a third-party SDK, legacy code — and its methods do not match your abstraction. Your checkout code calls PaymentProcessor.pay(rupees) ; the gateway's SDK offers makeTransaction(paise, currencyCode) . A GatewayAdapter implements PaymentProcessor and translates each call. The object adapter holds the adaptee (composition); the class adapter inherits from it, which needs multiple inheritance as in C++. In the JDK, InputStreamReader adapts a byte stream into a character reader, and Arrays.asList adapts an array into a List .

### Decorator

Intent. Attach extra responsibilities to an object at run time by wrapping it in another object with the same interface.

When to use. When features combine freely and a subclass per combination would explode — milk, sugar and caramel in any mix would need a class for every subset. Each decorator implements the same interface, holds the object it wraps, and adds its bit before or after delegating. Java's I/O streams are the textbook case: new BufferedReader(new InputStreamReader(stream)) . Python's @decorator syntax is a related idea applied to functions at definition time, not this pattern on objects.

Every add-on implements Coffee, so it can stand wherever a coffee is expected, and holds another Coffee as inner, so add-ons wrap each other in any order. Milk and Caramel only add their bit and delegate the rest.

```
#
include
<iostream>
#
include
<memory>
#
include
<string>
using
namespace
std
;
class
Coffee
{
// the shared interface
public
:
virtual
~
Coffee
(
)
=
default
;
virtual
string
describe
(
)
const
=
0
;
virtual
int
cost
(
)
const
=
0
;
}
;
class
Espresso
:
public
Coffee
{
public
:
string
describe
(
)
const
override
{
return
"espresso"
;
}
int
cost
(
)
const
override
{
return
100
;
}
}
;
class
AddOn
:
public
Coffee
{
// a decorator: is a Coffee and has a Coffee
protected
:
unique_ptr
<
Coffee
>
inner
;
public
:
explicit
AddOn
(
unique_ptr
<
Coffee
>
c
)
:
inner
(
move
(
c
)
)
{
}
}
;
class
Milk
:
public
AddOn
{
public
:
using
AddOn
::
AddOn
;
string
describe
(
)
const
override
{
return
inner
->
describe
(
)
+
" + milk"
;
}
int
cost
(
)
const
override
{
return
inner
->
cost
(
)
+
30
;
}
}
;
class
Caramel
:
public
AddOn
{
public
:
using
AddOn
::
AddOn
;
string
describe
(
)
const
override
{
return
inner
->
describe
(
)
+
" + caramel"
;
}
int
cost
(
)
const
override
{
return
inner
->
cost
(
)
+
45
;
}
}
;
int
main
(
)
{
unique_ptr
<
Coffee
>
plain
=
make_unique
<
Espresso
>
(
)
;
cout
<<
plain
->
describe
(
)
<<
" = Rs "
<<
plain
->
cost
(
)
<<
"\n"
;
unique_ptr
<
Coffee
>
order
=
make_unique
<
Caramel
>
(
make_unique
<
Milk
>
(
make_unique
<
Milk
>
(
make_unique
<
Espresso
>
(
)
)
)
)
;
cout
<<
order
->
describe
(
)
<<
" = Rs "
<<
order
->
cost
(
)
<<
"\n"
;
return
0
;
}
```

Output

```
espresso = Rs 100
espresso + milk + milk + caramel = Rs 205
```

new Caramel(new Milk(new Milk(new Espresso()))) builds a chain of four objects, each holding the next as inner. Only Espresso is a real drink; the others are wrappers that all look like a Coffee.

- new Caramel(new Milk(new Milk(new Espresso()))) builds a chain of four objects, each holding the next as inner. Only Espresso is a real drink; the others are wrappers that all look like a Coffee.
- order.cost() is called on the outermost wrapper. Each add-on first asks its inner coffee for its cost, so the call travels all the way down to the espresso.
- Espresso has nothing inside it: it returns its own price, 100, and the chain starts unwinding.
- Milk adds 30 to the 100 its inner coffee returned and returns 130.
- Milk adds 30 to the 130 its inner coffee returned and returns 160.
- Caramel adds 45 to the 160 its inner coffee returned and returns 205. describe() unwinds the same way, giving "espresso + milk + milk + caramel".

### Observer

Intent. Define a one-to-many dependency so that when one object (the subject ) changes state, all its dependents (the observers ) are notified automatically.

When to use. When several parts of a program must react to one object's changes and the subject should not know what they are: GUI event listeners, a model notifying its views, a price feed updating a display and an alert. Observers subscribe and unsubscribe at run time. Pitfalls: an observer that never unsubscribes keeps itself alive (a common memory leak, the "lapsed listener"); observers should not depend on notification order; and an observer that changes the subject during a notification can cause loops.

```
#
include
<algorithm>
#
include
<iostream>
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
class
PriceObserver
{
public
:
virtual
~
PriceObserver
(
)
=
default
;
virtual
void
onPrice
(
const
string
&
symbol
,
int
price
)
=
0
;
}
;
class
Ticker
{
// the subject: knows only the observer interface
string symbol
;
vector
<
PriceObserver
*
>
observers
;
// non-owning
public
:
explicit
Ticker
(
string s
)
:
symbol
(
s
)
{
}
void
subscribe
(
PriceObserver
*
o
)
{
observers
.
push_back
(
o
)
;
}
void
unsubscribe
(
PriceObserver
*
o
)
{
observers
.
erase
(
remove
(
observers
.
begin
(
)
,
observers
.
end
(
)
,
o
)
,
observers
.
end
(
)
)
;
}
void
setPrice
(
int
price
)
{
for
(
PriceObserver
*
o
:
observers
)
o
->
onPrice
(
symbol
,
price
)
;
// notify in subscription order
}
}
;
class
Display
:
public
PriceObserver
{
public
:
void
onPrice
(
const
string
&
s
,
int
p
)
override
{
cout
<<
"display: "
<<
s
<<
" = "
<<
p
<<
"\n"
;
}
}
;
class
Alert
:
public
PriceObserver
{
int
limit
;
public
:
explicit
Alert
(
int
limit
)
:
limit
(
limit
)
{
}
void
onPrice
(
const
string
&
s
,
int
p
)
override
{
if
(
p
>
limit
)
cout
<<
"alert: "
<<
s
<<
" above "
<<
limit
<<
" (now "
<<
p
<<
")\n"
;
}
}
;
int
main
(
)
{
Ticker
acme
(
"ACME"
)
;
Display display
;
Alert
alert
(
1550
)
;
acme
.
subscribe
(
&
display
)
;
acme
.
subscribe
(
&
alert
)
;
acme
.
setPrice
(
1500
)
;
acme
.
setPrice
(
1580
)
;
acme
.
unsubscribe
(
&
display
)
;
acme
.
setPrice
(
1610
)
;
return
0
;
}
```

Output

```
display: ACME = 1500
display: ACME = 1580
alert: ACME above 1550 (now 1580)
alert: ACME above 1550 (now 1610)
```

main subscribes a Display and an Alert to the ACME ticker. The ticker keeps them in a list and knows them only as PriceObserver, never as the concrete classes.

- main subscribes a Display and an Alert to the ACME ticker. The ticker keeps them in a list and knows them only as PriceObserver, never as the concrete classes.
- setPrice(1500): the ticker calls onPrice on each observer in subscription order. The display prints; the alert is called too, but 1500 is not above its limit of 1550, so it prints nothing.
- setPrice(1580): the same two calls in the same order. This time the price is above 1550, so both observers react.
- unsubscribe(display) removes the display from the list. Nothing else changes: the ticker still does not know or care what kind of objects it is notifying.
- setPrice(1610) notifies only the alert. Four lines in all, exactly the note's output: the subject never changed when its audience did.

### Strategy

Intent. Define a family of algorithms, put each behind a common interface, and make them interchangeable at run time.

When to use. When there are several ways to do one job and the choice depends on input or configuration: shipping cost rules, payment methods, sort orders, compression formats. It replaces a growing if / switch with one polymorphic call. Comparator passed to Collections.sort is a strategy; so is the key function in Python's sorted . Where functions are first-class, a strategy is often just a function, as the Python and JavaScript versions below show.

```
#
include
<iostream>
#
include
<memory>
#
include
<string>
using
namespace
std
;
class
ShippingStrategy
{
public
:
virtual
~
ShippingStrategy
(
)
=
default
;
virtual
string
name
(
)
const
=
0
;
virtual
int
cost
(
int
cartTotal
)
const
=
0
;
}
;
class
Standard
:
public
ShippingStrategy
{
public
:
string
name
(
)
const
override
{
return
"standard"
;
}
int
cost
(
int
total
)
const
override
{
return
total
>=
500
?
0
:
40
;
}
// free above Rs 500
}
;
class
Express
:
public
ShippingStrategy
{
public
:
string
name
(
)
const
override
{
return
"express"
;
}
int
cost
(
int
)
const
override
{
return
100
;
}
}
;
class
Pickup
:
public
ShippingStrategy
{
public
:
string
name
(
)
const
override
{
return
"pickup"
;
}
int
cost
(
int
)
const
override
{
return
0
;
}
}
;
class
Cart
{
int
total
;
unique_ptr
<
ShippingStrategy
>
shipping
;
public
:
explicit
Cart
(
int
total
)
:
total
(
total
)
,
shipping
(
make_unique
<
Standard
>
(
)
)
{
}
void
setShipping
(
unique_ptr
<
ShippingStrategy
>
s
)
{
shipping
=
move
(
s
)
;
}
// swap at run time
void
checkout
(
)
const
{
int
fee
=
shipping
->
cost
(
total
)
;
cout
<<
shipping
->
name
(
)
<<
": "
<<
total
<<
" + "
<<
fee
<<
" = "
<<
total
+
fee
<<
"\n"
;
}
}
;
int
main
(
)
{
Cart
cart
(
450
)
;
cart
.
checkout
(
)
;
cart
.
setShipping
(
make_unique
<
Express
>
(
)
)
;
cart
.
checkout
(
)
;
cart
.
setShipping
(
make_unique
<
Pickup
>
(
)
)
;
cart
.
checkout
(
)
;
Cart
big
(
800
)
;
big
.
checkout
(
)
;
return
0
;
}
```

Output

```
standard: 450 + 40 = 490
express: 450 + 100 = 550
pickup: 450 + 0 = 450
standard: 800 + 0 = 800
```

Cart calls shipping.cost(total) and never asks which rule it holds; setShipping swaps the object at run time. For a 450 cart the fees are 40, 100, 0, and Standard ships an 800 cart free.

### Common mistakes

- Reaching for a Singleton to avoid passing an object around; that is hidden global state.
- Writing double-checked locking in Java without volatile .
- Overriding __init__ in a Python singleton and being surprised that it runs on every Config() call.
- Calling any function that returns an object a "Factory Method"; the GoF pattern is about subclasses choosing the product.
- Forgetting to unsubscribe observers, so they are never garbage collected.
- Using a pattern because it is known rather than because the problem calls for it; patterns add classes.

### Interview questions

How do you make a Singleton thread-safe in Java? Four common ways: an eager private static final instance; the holder idiom, which creates the instance lazily when a nested class is first loaded; a single-element enum ; or double-checked locking on a volatile field. A synchronized accessor also works but takes a lock on every call. The holder idiom and the enum are the usual recommendations.

How can a Java Singleton be broken, and how do you prevent it? Reflection can call the private constructor after setAccessible(true) ; deserialising a serialised instance creates a new object; and clone() could copy it if the class were cloneable. An enum singleton is protected against reflection and serialisation by the language; for a class, throw from the constructor if an instance exists and add readResolve() returning the instance.

What is the difference between Decorator and Proxy? Both wrap an object behind the same interface. A Decorator adds behaviour, and decorators are designed to be stacked in any combination. A Proxy controls access to the object — lazy loading, access checks, remote calls, caching — and usually manages that object's lifecycle itself.

What is the difference between Adapter and Facade? An Adapter converts one existing interface into a different interface that a client already expects; it is about compatibility. A Facade offers a new, simpler interface over a whole subsystem of classes, such as one placeOrder() hiding inventory, payment and shipping; it is about convenience.

What is the difference between Strategy and Template Method? Both let a step of an algorithm vary. Template Method uses inheritance: a base class fixes the outline and subclasses override steps, so the choice is fixed per class. Strategy uses composition: the varying part is a separate object passed in, so it can change at run time.

Name design patterns used in the Java standard library. Iterator in java.util.Iterator ; Decorator in the java.io streams; Adapter in InputStreamReader ; Strategy in Comparator ; Observer in GUI event listeners; Builder in StringBuilder and HttpRequest.Builder ; Singleton in Runtime.getRuntime() . Naming the pattern and the class together is what interviewers look for.

When should you not use a design pattern? When the problem it solves is not present. A pattern adds indirection and classes; applying Strategy to logic with one variant, or a Factory for a class created in one place, makes the code harder to read for no gain. Introduce the pattern when the second or third variant actually appears.

Next, read Object Equality, Hashing and Copying , then check yourself with the OOP Intermediate skill test .

### What are the three types of design patterns?

Creational patterns deal with how objects are created (Singleton, Factory Method, Abstract Factory, Builder, Prototype). Structural patterns deal with how classes and objects are combined into larger structures (Adapter, Decorator, Facade, Proxy and others). Behavioural patterns deal with how objects communicate and share responsibility (Observer, Strategy, Command, Iterator and others).

### Who are the Gang of Four?

Erich Gamma, Richard Helm, Ralph Johnson and John Vlissides, authors of Design Patterns: Elements of Reusable Object-Oriented Software, published in 1994. The book described 23 patterns with C++ and Smalltalk examples and gave the industry the shared names, such as Singleton and Observer, that interviews still use.

### What is the difference between Factory Method and Abstract Factory?

Factory Method is a single method, overridden by subclasses, that decides which concrete class to instantiate for one kind of product. Abstract Factory is an object with several creation methods that produces a whole family of related products, such as buttons and checkboxes that all match one operating system's look.

### Is Singleton an anti-pattern?

It is often called one, because a singleton is global state in disguise: classes reach for it instead of receiving it, which hides dependencies and makes tests share state. It is reasonable for things that genuinely exist once per process, such as a logger or a configuration object, ideally still passed to the classes that use it.

### What is the difference between Strategy and State patterns?

Both delegate behaviour to a swappable object behind an interface. In Strategy the client chooses the algorithm and the strategies know nothing about each other. In State the object switches its own state object as events happen, and each state usually decides which state comes next, as in an order moving from placed to shipped.

### How is the Observer pattern different from publish-subscribe?

In Observer the subject keeps a direct list of its observers and calls them itself, usually synchronously. In publish-subscribe a broker or event channel sits between them: publishers and subscribers do not know about each other, and delivery is often asynchronous, as with message queues.


---

## Module 9: Association, Aggregation and Composition

*Original URL: https://codekairo.com/notes/oop/association-aggregation-composition*

### Overview

Quick answer

### What is the difference between association, aggregation and composition in OOP?

All three are has-a relationships, from weakest to strongest. Association means one object knows about or uses another and both live independently. Aggregation is a whole-part association whose parts can exist without the whole, like a team and its players. Composition is whole-part with ownership: the whole creates its parts and they end with it, like a house and its rooms.

- How classes relate
- Association
- Aggregation
- Composition
- How the relationships look in code
- Composition over inheritance
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Inheritance is not the only way for classes to work together, and usually not the best one. Most relationships in a real design are has-a : an order has order lines, a car has an engine, a course has students. OOP names three strengths of has-a — association , aggregation and composition — and the difference between them is about ownership and lifetime : who creates the other object, who else may hold it, and whether it outlives its holder. Interviewers ask about these to see whether you can model a system, and they almost always follow up with "composition over inheritance".

### How classes relate

Read the middle three as a scale. Every composition is an aggregation, and every aggregation is an association; each step adds a stronger claim about ownership.

A plain line is an association; a hollow diamond on the whole is aggregation; a filled diamond on the whole is composition; a hollow triangle on the parent is inheritance. The numbers are multiplicities: how many objects sit at that end.

### Association

An association is any lasting link between objects of two classes, where neither owns the other. A teacher teaches students; a student is taught by teachers; either can exist without the other.

Two properties describe an association:

- Multiplicity — how many objects on each side: one-to-one (a person and their passport), one-to-many (a customer and their orders), many-to-many (teachers and students).
- Direction — whether one side knows the other (unidirectional: an Order knows its Customer , but the customer object does not list orders) or both do (bidirectional). Bidirectional links must be kept consistent by code: adding a student to a teacher should also add the teacher to the student.

A dependency is weaker than association: the class only uses the other one inside a method, as a parameter or a local variable, and keeps no reference afterwards.

### Aggregation

Aggregation is a whole-part association in which the whole does not own its parts. The parts are typically created elsewhere and handed to the whole; they can be shared between several wholes; and when the whole is destroyed, the parts carry on.

- A team aggregates players : disband the team and the players still exist and can join another.
- A department aggregates professors : a professor can hold appointments in two departments.
- A playlist aggregates songs : deleting a playlist does not delete the songs.

### Composition

Composition is a whole-part relationship with exclusive ownership. The whole creates its parts (or receives sole ownership of them), no other object holds them, and they are destroyed together with the whole. The part does not make sense on its own in the model.

- A house is composed of rooms : demolish the house and the rooms are gone.
- An order is composed of order lines : an order line belongs to exactly one order.
- A document is composed of its paragraphs .

Whether a relationship is aggregation or composition depends on the system you are modelling , not on the real world. In a car-rental app, an engine is part of a car and nobody tracks it separately: composition. In a scrapyard's inventory, engines are removed and resold on their own: aggregation. Say this in an interview; it shows you are modelling, not reciting.

### How the relationships look in code

C++ makes ownership visible in the types: unique_ptr means "I am the only owner", shared_ptr means "we share ownership", and a raw pointer or reference means "I use this but do not own it". In Java and Python the garbage collector frees an object only when it becomes unreachable, so composition there is a design promise: if a Car leaks a reference to its Engine , the engine can outlive the car.

The program below models a car that composes its engine — it builds the engine in its own constructor — and aggregates a driver created outside it. The car's start() delegates to its engine: it forwards the work to the part it holds.

Car builds its Engine in its own constructor and never hands it out: composition, exactly one engine per car. Its driver is set later through assign() and may be null: aggregation, zero or one driver per car, while one driver can drive any number of cars.

```
#
include
<iostream>
#
include
<string>
using
namespace
std
;
class
Engine
{
// a part: only ever created by a Car
int
cc
;
public
:
explicit
Engine
(
int
cc
)
:
cc
(
cc
)
{
}
string
start
(
)
const
{
return
to_string
(
cc
)
+
"cc engine started"
;
}
}
;
class
Driver
{
// independent: exists before and after any car
string name
;
int
trips
=
0
;
public
:
explicit
Driver
(
string name
)
:
name
(
name
)
{
}
void
recordTrip
(
)
{
trips
++
;
}
string
getName
(
)
const
{
return
name
;
}
int
getTrips
(
)
const
{
return
trips
;
}
}
;
class
Car
{
string reg
;
Engine engine
;
// composition: the car builds and owns its engine
Driver
*
driver
=
nullptr
;
// aggregation: the car only refers to a driver
public
:
Car
(
string reg
,
int
cc
)
:
reg
(
reg
)
,
engine
(
cc
)
{
}
void
assign
(
Driver
&
d
)
{
driver
=
&
d
;
}
void
start
(
)
{
driver
->
recordTrip
(
)
;
cout
<<
reg
<<
": "
<<
engine
.
start
(
)
<<
", driven by "
<<
driver
->
getName
(
)
<<
"\n"
;
// delegation
}
}
;
int
main
(
)
{
Driver
asha
(
"Asha"
)
;
{
Car
first
(
"KA-01-1234"
,
1197
)
;
first
.
assign
(
asha
)
;
first
.
start
(
)
;
}
// first and its engine are destroyed here; asha is not
Car
second
(
"KA-05-9876"
,
1462
)
;
second
.
assign
(
asha
)
;
second
.
start
(
)
;
cout
<<
asha
.
getName
(
)
<<
" has driven "
<<
asha
.
getTrips
(
)
<<
" cars\n"
;
return
0
;
}
```

Output

```
KA-01-1234: 1197cc engine started, driven by Asha
KA-05-9876: 1462cc engine started, driven by Asha
Asha has driven 2 cars
```

Driver asha = new Driver("Asha"): a driver exists on its own, before any car, and only the variable asha refers to it.

- Driver asha = new Driver("Asha"): a driver exists on its own, before any car, and only the variable asha refers to it.
- new Car("KA-01-1234", 1197) builds its Engine inside the constructor. The car is the only thing holding that engine: composition.
- first.assign(asha) stores a reference to a driver the car did not create. Two references now reach the driver: aggregation.
- first.start() delegates to its engine's start() and records a trip on the driver, whose trips becomes 1.
- first = null leaves the car unreachable. The engine was reachable only through the car, so the collector frees both; asha still reaches the driver, so the driver lives on.
- A second car is built with an engine of its own, and the same driver is assigned to it: one part shared over time by two wholes.
- second.start() records the driver's second trip. The driver outlived the first car and its engine, and has driven 2 cars.

C++ can show the lifetimes directly, because destructors run at a known moment. The house holds its rooms as members; the department holds only pointers to professors created outside it:

```
#
include
<iostream>
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
struct
Room
{
string name
;
explicit
Room
(
string n
)
:
name
(
n
)
{
}
~
Room
(
)
{
cout
<<
"room "
<<
name
<<
" destroyed\n"
;
}
}
;
class
House
{
// composition: rooms are members, owned by value
Room kitchen
{
"kitchen"
}
;
Room bedroom
{
"bedroom"
}
;
public
:
~
House
(
)
{
cout
<<
"house destroyed\n"
;
}
}
;
struct
Professor
{
string name
;
explicit
Professor
(
string n
)
:
name
(
n
)
{
}
~
Professor
(
)
{
cout
<<
"professor "
<<
name
<<
" destroyed\n"
;
}
}
;
class
Department
{
// aggregation: pointers to professors it does not own
vector
<
Professor
*
>
staff
;
public
:
void
hire
(
Professor
*
p
)
{
staff
.
push_back
(
p
)
;
}
~
Department
(
)
{
cout
<<
"department closed, "
<<
staff
.
size
(
)
<<
" professors released\n"
;
}
}
;
int
main
(
)
{
Professor
rao
(
"Rao"
)
,
iyer
(
"Iyer"
)
;
// created outside any department
{
cout
<<
"house goes out of scope:\n"
;
House h
;
}
{
Department cse
;
cse
.
hire
(
&
rao
)
;
cse
.
hire
(
&
iyer
)
;
cout
<<
"department goes out of scope:\n"
;
}
cout
<<
"professors still here: "
<<
rao
.
name
<<
", "
<<
iyer
.
name
<<
"\n"
;
cout
<<
"main ends:\n"
;
return
0
;
}
```

Output

```
house goes out of scope:
house destroyed
room bedroom destroyed
room kitchen destroyed
department goes out of scope:
department closed, 2 professors released
professors still here: Rao, Iyer
main ends:
professor Iyer destroyed
professor Rao destroyed
```

main creates two professors, rao and iyer, before any department exists. They belong to main's scope.

- main creates two professors, rao and iyer, before any department exists. They belong to main's scope.
- Inside the first block, House h is built. Its rooms are members held by value: they are constructed first, in declaration order, and live inside the house.
- The block ends. ~House runs first, then its members are destroyed in reverse order of declaration: the house, then bedroom, then kitchen. Composition: the parts cannot outlive the whole.
- Department cse hires &rao and &iyer: its staff vector holds 2 pointers to professors it did not create.
- The second block ends and only the department is destroyed. Its vector of pointers goes, but a pointer's destruction never touches what it points at: aggregation.
- The professors are still there when main ends, and are destroyed as its locals: in reverse order of construction, iyer before rao.

### Composition over inheritance

The Design Patterns book (Gamma, Helm, Johnson and Vlissides, 1994) put it as "favor object composition over class inheritance". The reasons:

- Inheritance exposes everything. A subclass inherits every public method of its parent, including ones that break its own rules.
- Inheritance couples you to the parent's internals. A change inside the parent can break the child — the fragile base class problem.
- Inheritance is fixed when you write the class. Composition lets you choose or swap the parts at run time.
- Inheritance multiplies classes. Combining three kinds of storage with two kinds of logging needs six subclasses; with composition it needs five small classes plugged together.

Java's own library has the classic example: java.util.Stack extends Vector , so a "stack" also offers add(0, x) and get(i) , and anyone can insert at the bottom. The Java documentation now recommends ArrayDeque instead. The program below builds a stack by inheriting from a list, shows the hole, then builds one by composition, which offers only stack operations:

```
#
include
<iostream>
#
include
<stdexcept>
#
include
<vector>
using
namespace
std
;
class
InheritedStack
:
public
vector
<
int
>
{
// is-a vector: every vector operation leaks through
public
:
// (std::vector is not meant to be a base class either)
void
push
(
int
x
)
{
push_back
(
x
)
;
}
}
;
class
Stack
{
// has-a vector: only stack operations exist
vector
<
int
>
items
;
public
:
void
push
(
int
x
)
{
items
.
push_back
(
x
)
;
}
int
pop
(
)
{
if
(
items
.
empty
(
)
)
throw
out_of_range
(
"pop from empty stack"
)
;
int
top
=
items
.
back
(
)
;
items
.
pop_back
(
)
;
return
top
;
}
int
peek
(
)
const
{
return
items
.
back
(
)
;
}
size_t
size
(
)
const
{
return
items
.
size
(
)
;
}
}
;
int
main
(
)
{
InheritedStack bad
;
bad
.
push
(
1
)
;
bad
.
push
(
2
)
;
bad
.
insert
(
bad
.
begin
(
)
,
99
)
;
// inserting at the bottom of a "stack" compiles fine
cout
<<
"inherited stack: ["
<<
bad
[
0
]
<<
", "
<<
bad
[
1
]
<<
", "
<<
bad
[
2
]
<<
"]\n"
;
Stack s
;
for
(
int
x
:
{
10
,
20
,
30
}
)
s
.
push
(
x
)
;
cout
<<
"pop: "
<<
s
.
pop
(
)
<<
"\n"
;
cout
<<
"peek: "
<<
s
.
peek
(
)
<<
"\n"
;
cout
<<
"size: "
<<
s
.
size
(
)
<<
"\n"
;
s
.
pop
(
)
;
s
.
pop
(
)
;
try
{
s
.
pop
(
)
;
}
catch
(
const
out_of_range
&
e
)
{
cout
<<
"error: "
<<
e
.
what
(
)
<<
"\n"
;
}
return
0
;
}
```

Output

```
inherited stack: [99, 1, 2]
pop: 30
peek: 20
size: 2
error: pop from empty stack
```

Inheriting from list hands callers all 11 of list's methods, so insert(0, 99) puts a value at the bottom of a "stack". Holding the list as a private part exposes only the 4 methods Stack chose to write.

Inheritance is still the right tool when the is-a relationship is real and a child can stand in for its parent everywhere — the Liskov Substitution Principle in SOLID Principles . Composition is the default for reuse.

### Common mistakes

- Treating "has-a" as a synonym for composition; aggregation and plain association are has-a as well.
- Deciding aggregation versus composition from the real world instead of from the system being modelled.
- Returning a composed part from a getter, which lets it escape and outlive its owner.
- Holding shared_ptr on both sides of a bidirectional C++ link; the cycle never frees, so one side should be a weak_ptr or raw pointer.
- Inheriting from a collection class to "reuse" it, exposing every collection method.
- Drawing the UML diamond at the part's end instead of the whole's.

### Interview questions

Give an example where the same pair is aggregation in one system and composition in another. An engine and a car. In a car-rental system nobody tracks engines separately, so the car composes its engine. In a scrapyard inventory, engines are pulled out, stored and sold on their own, so a car only aggregates one. The model's needs decide, not the physical objects.

How do you implement composition in Java, given the garbage collector? Create the part inside the whole's constructor, keep it in a private final field, and never return it — return copies or derived values instead. The garbage collector then frees the part when the whole becomes unreachable, because nothing else refers to it.

How does modern C++ express ownership? std::unique_ptr for sole ownership (composition), std::shared_ptr for shared ownership, and a raw pointer or reference for a non-owning link (association or aggregation). std::weak_ptr observes a shared object without keeping it alive, which breaks reference cycles.

What is the difference between association and dependency? An association is a lasting structural link: one class keeps a reference to the other as a field. A dependency is a temporary use: the class receives the other as a method parameter or creates it as a local variable and forgets it when the method returns.

What is delegation? Delegation is forwarding a request to a contained object instead of handling it yourself: Car.start() calls engine.start() . Composition plus delegation gives you reuse without inheritance, and you choose exactly which of the part's methods to expose.

Why is java.util.Stack often cited as a design mistake? It extends Vector , so it inherits methods like add(int, E) , get(int) and remove(int) that let callers bypass last-in-first-out order. A stack is not a vector; it should have held one. The documentation points to Deque implementations such as ArrayDeque instead.

When is inheritance a better choice than composition? When the subclass truly is a kind of the parent and can replace it anywhere without surprises, and especially when a framework is designed to be extended through subclasses. Even then, keep hierarchies shallow and the parent's extension points explicit.

Next, read SOLID Principles , then check yourself with the OOP Intermediate skill test .

### What is a has-a relationship in OOP?

A has-a relationship means one object holds a reference to another as a field: a Car has an Engine, a Department has Professors. It is the alternative to inheritance's is-a relationship, and it covers association, aggregation and composition, which differ in how strongly the holder owns the object it holds.

### What is the difference between aggregation and composition?

Both are whole-part relationships. In aggregation the parts have their own life: they are usually created elsewhere, can be shared, and survive when the whole is destroyed. In composition the whole owns its parts exclusively: it creates them, nobody else holds them, and they are destroyed with it.

### What does composition over inheritance mean?

It is the design guideline, popularised by the Gang of Four's Design Patterns book, to reuse behaviour by holding objects that provide it rather than by inheriting from them. Composition exposes only the methods you choose, can swap parts at run time and does not tie a class to its parent's internals.

### How are aggregation and composition drawn in UML?

Both are a line between the two classes with a diamond at the whole's end. Aggregation uses a hollow diamond and composition a filled, black diamond. A plain line is an association, a dashed arrow is a dependency, and a line ending in a hollow triangle is inheritance.

### Can a part belong to two wholes?

In aggregation, yes: a professor can belong to two departments, a song to many playlists. In composition, no: a part has exactly one owner at a time, which is what lets the owner destroy it safely. Ownership can be transferred, as with std::unique_ptr in C++, but never shared.


---

## Module 10: Object Equality, Hashing and Copying

*Original URL: https://codekairo.com/notes/oop/object-equality-and-copying*

### Overview

Quick answer

### What is the difference between object identity and object equality?

Identity asks whether two references point to the very same object; equality asks whether two possibly different objects hold the same value. Java tests identity with == and equality with equals(), Python uses is and ==, and C++ compares addresses for identity and calls operator== for value. A class that defines equality must define a matching hash code too.

- Identity vs equality
- Defining equality
- The hashCode contract
- Shallow vs deep copy
- Copy constructors and assignment in C++
- Immutability makes copying unnecessary
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Two of the most common bugs in object-oriented code look identical on the surface: a set that "contains" an object yet says it does not, and a copy that changes when you edit the original. Both come from mixing up what an object is (its identity) with what it holds (its value). This note pins down identity versus equality in C++, Java and Python, the contract between equality and hashing that every hash-based collection relies on, and the difference between shallow and deep copies — including how C++ copy constructors and assignment operators must be written when a class owns memory. It assumes Classes and Objects , especially what a variable holds in each language.

### Identity vs equality

- Identity : are these two references the same object ? There is one object, reached by two names.
- Equality : do these two objects have the same value ? There may be two separate objects that are interchangeable for the program's purposes, like two Point(1, 2) s.

Two Java traps follow from == meaning identity. String literals are interned — one shared object per distinct literal — so "hi" == "hi" is true, while new String("hi") == "hi" is false; always compare strings with equals . And boxed integers from -128 to 127 come from a cache, so Integer a = 127, b = 127; a == b is true but the same with 128 is false. Python has a similar implementation detail — CPython caches small integers — which is why is should be used only for None and genuine identity checks.

Two new Point(1, 2) calls make two objects. p == q compares the references, which differ, so it is false; p.equals(q) compares the fields the class chose, so it is true.

- Two new Point(1, 2) calls make two objects. p == q compares the references, which differ, so it is false; p.equals(q) compares the fields the class chose, so it is true.
- String literals are interned: every "hi" in the program is one shared object in the pool, so s1 == s2 is true. new String("hi") always builds another object, so == fails where equals still succeeds.
- Autoboxing calls Integer.valueOf, which hands out one cached object for each value from -128 to 127. Both 127s get the cached one, so a == b; each 128 is a new object, so c == d is false.

### Defining equality

A class that represents a value (a point, a money amount, a date) should define equality on its significant fields. Java's equals contract requires the relation to be:

- reflexive — x.equals(x) is true;
- symmetric — x.equals(y) exactly when y.equals(x) ;
- transitive — if x.equals(y) and y.equals(z) , then x.equals(z) ;
- consistent — repeated calls give the same answer while the objects are unchanged;
- and x.equals(null) is false .

The usual recipe: return true for the same reference; return false for null or a different class; then compare the significant fields. Using getClass() != o.getClass() keeps symmetry safe when subclasses add fields; instanceof lets subclasses compare equal to their parent but can break symmetry if a subclass overrides equals . Java 16 records generate a correct equals , hashCode and toString from their components. Python's @dataclass generates __eq__ ; a hand-written __eq__ should return NotImplemented for types it does not understand, so Python can try the other operand.

### The hashCode contract

Hash tables — HashMap , HashSet , Python's dict and set , C++'s unordered_map — find an object in two steps: the hash code picks a bucket, then equality confirms the match among the objects in that bucket. That only works if the two agree:

- Equal objects must have equal hash codes. Break this, and an equal object is looked for in the wrong bucket and never found.
- A hash code must stay the same while the object's fields are unchanged.
- Unequal objects may share a hash code — a collision. It is legal but slows lookups. "Aa" and "BB" have the same String.hashCode() , 2112.

add(p): Objects.hash(1, 2) is 994. HashMap spreads it and keeps the low four bits, (h ^ (h >>> 16)) & 15, which picks bucket 2 of the table's 16. The point is stored there.

- add(p): Objects.hash(1, 2) is 994. HashMap spreads it and keeps the low four bits, (h ^ (h >>> 16)) & 15, which picks bucket 2 of the table's 16. The point is stored there.
- contains(q): q is a different object with the same fields, so the same hash, 994, leads to the same bucket. Only there is equals called, once, and it says yes.
- add(q) finds the equal point already in bucket 2 and does nothing, so the set's size stays 1 — the note's output. With equals but no matching hashCode, q would have gone to another bucket and never been compared.
- A collision: "Aa" and "BB" are unequal but both have String.hashCode 2112, so both land in bucket 0. That is legal; equals tells them apart, and the set holds both. Collisions cost time, not correctness.

Build the hash from exactly the fields that equals compares — Objects.hash(x, y) in Java, hash((self.x, self.y)) in Python. The program below defines both and shows that a hash set treats two separate but equal points as one element:

```
#
include
<functional>
#
include
<iostream>
#
include
<unordered_set>
using
namespace
std
;
struct
Point
{
int
x
,
y
;
bool
operator
==
(
const
Point
&
o
)
const
{
return
x
==
o
.
x
&&
y
==
o
.
y
;
}
// value equality
}
;
struct
PointHash
{
// equal points must produce equal hashes
size_t
operator
(
)
(
const
Point
&
p
)
const
{
return
hash
<
int
>
(
)
(
p
.
x
)
*
31
+
hash
<
int
>
(
)
(
p
.
y
)
;
}
}
;
int
main
(
)
{
Point p
{
1
,
2
}
,
q
{
1
,
2
}
;
cout
<<
"same object: "
<<
(
&
p
==
&
q
?
"yes"
:
"no"
)
<<
"\n"
;
cout
<<
"equal values: "
<<
(
p
==
q
?
"yes"
:
"no"
)
<<
"\n"
;
unordered_set
<
Point
,
PointHash
>
seen
;
seen
.
insert
(
p
)
;
cout
<<
"set contains an equal point: "
<<
(
seen
.
count
(
q
)
?
"yes"
:
"no"
)
<<
"\n"
;
seen
.
insert
(
q
)
;
cout
<<
"set size after adding both: "
<<
seen
.
size
(
)
<<
"\n"
;
return
0
;
}
```

Output

```
same object: no
equal values: yes
set contains an equal point: yes
set size after adding both: 1
```

What happens when the contract is broken differs by language. In Java, overriding only equals compiles fine and fails quietly: contains usually returns false and a set can hold "duplicates". Python is stricter: a class that defines __eq__ without __hash__ has its __hash__ set to None , so it cannot be put in a set or used as a dict key at all:

```
class
Point
:
def
__init__
(
self
,
x
,
y
)
:
self
.
x
,
self
.
y
=
x
,
y
def
__eq__
(
self
,
other
)
:
return
isinstance
(
other
,
Point
)
and
(
self
.
x
,
self
.
y
)
==
(
other
.
x
,
other
.
y
)
print
(
f"__hash__ is None:
{
Point
.
__hash__
is
None
}
"
)
try
:
{
Point
(
1
,
2
)
}
except
TypeError
as
e
:
print
(
f"TypeError:
{
e
}
"
)
```

Output

```
__hash__ is None: True
TypeError: unhashable type: 'Point'
```

One more rule follows: do not mutate an object while it is a key in a hash map or an element of a hash set. Its hash changes, it now sits in the wrong bucket, and the collection can no longer find it. Immutable keys avoid the problem entirely.

### Shallow vs deep copy

A shallow copy is a new object whose fields are copied as they are. A field holding a number or an immutable string is effectively independent; a field holding a reference to a mutable object — a list, an array, another object — still points at the same object as the original. A deep copy also copies those referenced objects, recursively, so nothing mutable is shared.

```
#
include
<iostream>
#
include
<memory>
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
string
joined
(
const
vector
<
string
>
&
v
)
{
string out
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
out
+=
(
i
?
", "
:
""
)
+
v
[
i
]
;
return
out
;
}
struct
Team
{
string name
;
shared_ptr
<
vector
<
string
>>
players
;
// a pointer member: copying a Team shares the list
Team
deepCopy
(
)
const
{
return
Team
{
name
,
make_shared
<
vector
<
string
>>
(
*
players
)
}
;
}
}
;
int
main
(
)
{
Team original
{
"Blue"
,
make_shared
<
vector
<
string
>>
(
vector
<
string
>
{
"Asha"
,
"Ravi"
}
)
}
;
Team shallow
=
original
;
// the default copy copies the pointer, not the list
shallow
.
players
->
push_back
(
"Kiran"
)
;
shallow
.
name
=
"Red"
;
// reassigning the copy's own field
cout
<<
"original after shallow.players gains Kiran: "
<<
joined
(
*
original
.
players
)
<<
"\n"
;
cout
<<
"original name after shallow is renamed: "
<<
original
.
name
<<
"\n"
;
Team deep
=
original
.
deepCopy
(
)
;
deep
.
players
->
push_back
(
"Meera"
)
;
cout
<<
"original after deep.players gains Meera: "
<<
joined
(
*
original
.
players
)
<<
"\n"
;
cout
<<
"deep copy: "
<<
joined
(
*
deep
.
players
)
<<
"\n"
;
return
0
;
}
```

Output

```
original after shallow.players gains Kiran: Asha, Ravi, Kiran
original name after shallow is renamed: Blue
original after deep.players gains Meera: Asha, Ravi, Kiran
deep copy: Asha, Ravi, Kiran, Meera
```

original is a Team whose players field refers to a list object holding Asha and Ravi. The name is an immutable string, so it can be thought of as a value.

- original is a Team whose players field refers to a list object holding Asha and Ravi. The name is an immutable string, so it can be thought of as a value.
- copy.copy(original) makes a new Team and copies each field as it is. The players field holds a reference, so the copy refers to the very same list: one list, two owners.
- shallow.players.append("Kiran") changes that shared list, so the original sees Kiran too — the first line the program prints.
- shallow.name = "Red" reassigns a field of the copy alone. Reassigning is not mutating: the original's name is still Blue.
- copy.deepcopy(original) copies the list as well, so deep gets a list of its own holding the same three names.
- deep.players.append("Meera") touches only deep's list. The original still has three players; nothing mutable is shared any more.

copy.deepcopy keeps a memo of objects already copied, so two fields pointing at one object still point at one (new) object in the copy, and cyclic structures do not recurse forever.

### Copy constructors and assignment in C++

In C++, Team b = a; calls the copy constructor (a new object is being created), while b = a; on an existing b calls the copy assignment operator . The compiler generates both, copying member by member. That is correct for members such as std::vector and std::string , which copy their own contents — but wrong for a class that owns a raw pointer: both objects would point at one array, and both destructors would free it.

The rule of three : if a class needs a user-written destructor, copy constructor or copy assignment operator, it almost certainly needs all three. C++11 extends it to the rule of five by adding the move constructor and move assignment. The rule of zero is the modern advice: hold resources in members that manage themselves ( std::vector , std::unique_ptr ) and write none of them.

The copy-and-swap idiom writes the assignment operator once, safely: take the parameter by value (the copy constructor makes the copy), swap its contents into *this , and let the parameter's destructor free the old data. It handles self-assignment and gives the strong exception guarantee, because nothing in *this changes until the copy has succeeded.

```
#
include
<algorithm>
#
include
<iostream>
#
include
<utility>
using
namespace
std
;
class
Buffer
{
// owns a heap array, so it defines its own copying (rule of three)
size_t n
;
int
*
data
;
public
:
explicit
Buffer
(
size_t n
)
:
n
(
n
)
,
data
(
new
int
[
n
]
(
)
)
{
}
Buffer
(
const
Buffer
&
o
)
:
n
(
o
.
n
)
,
data
(
new
int
[
o
.
n
]
)
{
// copy constructor: a deep copy
copy
(
o
.
data
,
o
.
data
+
n
,
data
)
;
cout
<<
"copy constructor\n"
;
}
Buffer
&
operator
=
(
Buffer o
)
{
// copy-and-swap: o is already a fresh copy
swap
(
n
,
o
.
n
)
;
swap
(
data
,
o
.
data
)
;
cout
<<
"copy assignment\n"
;
return
*
this
;
}
// o's destructor frees the old array
~
Buffer
(
)
{
delete
[
]
data
;
}
int
&
operator
[
]
(
size_t i
)
{
return
data
[
i
]
;
}
}
;
int
main
(
)
{
Buffer
a
(
3
)
;
a
[
0
]
=
7
;
Buffer b
=
a
;
// copy constructor: b is a new object
b
[
0
]
=
99
;
// does not touch a
Buffer
c
(
1
)
;
c
=
a
;
// copy assignment; its by-value parameter is built by the copy constructor
c
=
c
;
// self-assignment is safe with copy-and-swap
cout
<<
"a[0] = "
<<
a
[
0
]
<<
", b[0] = "
<<
b
[
0
]
<<
", c[0] = "
<<
c
[
0
]
<<
"\n"
;
return
0
;
}
```

Output

```
copy constructor
copy constructor
copy assignment
copy constructor
copy assignment
a[0] = 7, b[0] = 99, c[0] = 7
```

Buffer a(3) owns a heap array of three ints through a raw pointer, and a[0] = 7 writes into it.

- Buffer a(3) owns a heap array of three ints through a raw pointer, and a[0] = 7 writes into it.
- If Buffer relied on the compiler's copy, b = a would copy the pointer: two objects owning one array, and both destructors would delete[] it. That is why a class like this needs its own copy constructor.
- The user-written copy constructor allocates a fresh array and copies the values, so b[0] = 99 changes only b's array.
- Buffer c(1) gets an array of its own. Next, c = a calls the assignment operator, whose parameter is taken by value.
- Taking the parameter by value runs the copy constructor, building o as a copy of a. The body then swaps n and data with o: c now owns the copy, and o holds c's old array.
- operator= returns and o is destroyed, freeing the array that used to be c's. If the copy had thrown, c would never have been touched: the strong guarantee.
- c = c runs the same steps: copy, swap, free the old array. Self-assignment needs no special check, and the program ends with a[0] = 7, b[0] = 99 and c[0] = 7.

### Immutability makes copying unnecessary

An immutable object can be shared freely: nobody can change it, so there is nothing to protect with a copy. Java's String and Integer , Python's str , int and frozenset , and Java records holding immutable fields are all safe to share and safe as hash keys. Watch for shallow immutability: a Python tuple holding a list , or a final Java field holding an ArrayList , can still change inside. Encapsulation shows how to build immutable classes with defensive copies.

### Common mistakes

- Comparing Java strings or boxed numbers with == instead of equals .
- Overriding equals without hashCode (Java) or __eq__ without __hash__ (Python).
- Writing equals(Point other) in Java, which overloads instead of overriding equals(Object) ; @Override catches it.
- Using a mutable object as a hash key and changing it afterwards.
- Assuming clone() or copy.copy copies nested lists; both are shallow.
- Giving a C++ class that owns a raw pointer a destructor but no copy constructor or assignment operator.

### Interview questions

What happens if you override equals but not hashCode in Java? The code compiles, but hash-based collections misbehave: two equal objects almost always have different identity-based hash codes, so HashSet.contains and HashMap.get look in the wrong bucket and miss. A set can then hold two "equal" elements. Overriding both, from the same fields, fixes it.

Can two unequal objects have the same hash code? Yes; that is a collision, and the contract allows it. Hash codes are 32-bit integers, so collisions are unavoidable — "Aa" and "BB" share String.hashCode() 2112. Collisions only cost speed, because the collection then calls equals to tell the objects apart.

Should equals use getClass() or instanceof? getClass() treats objects of different classes as unequal, which keeps equals symmetric when a subclass adds fields. instanceof lets a subclass instance equal a parent instance, which is right when subclasses add no state that matters for equality, but it breaks symmetry if a subclass also overrides equals . Making value classes final avoids the question.

Why is clone() considered a poor way to copy in Java? Cloneable has no clone method of its own, Object.clone() is protected, shallow and throws a checked exception, and it bypasses constructors, so it cannot assign final fields a new deep copy. Effective Java recommends a copy constructor or copy factory instead.

When does a C++ class need a user-defined copy constructor? When member-by-member copying is wrong — typically when the class owns a resource through a raw pointer or handle. The default copy would make two objects share one resource and free it twice. By the rule of three, such a class also needs a destructor and a copy assignment operator, and under C++11 usually move operations as well.

Why is a mutable object a dangerous HashMap key? The map stores the key in the bucket chosen by its hash code at insertion time. If a field that feeds the hash changes, lookups compute a different bucket and the entry is effectively lost while still taking up space. Use immutable keys, or never change a key while it is in the map.

How does Python's deepcopy handle shared references and cycles? It keeps a memo dictionary from each original object's id to its copy. When it meets an object it has already copied, it reuses that copy, so shared structure stays shared in the copy and a cycle ends instead of recursing forever. Classes can customise the process with __deepcopy__ .

Why can == on two Java strings sometimes be true? String literals and compile-time constant expressions are interned, so every occurrence of the same literal refers to one shared object, and == happens to see the same reference. Strings built at run time, read from input or created with new String , are separate objects. Relying on this is a bug; use equals .

Next, read Exception Handling in OOP , then check yourself with the OOP Intermediate skill test .

### What is the difference between == and equals() in Java?

For objects, == compares references: it is true only when both sides are the same object. equals() compares values as the class defines them; Object's default equals() is also identity, so a class must override it to compare fields. String, Integer and the collections override it, which is why strings are compared with equals().

### Why must hashCode be overridden when equals is overridden?

Hash-based collections such as HashMap and HashSet find an object by its hash code first and only then call equals. If two equal objects return different hash codes, they land in different buckets and the collection never compares them, so contains() returns false for an object that is equal to one already stored.

### What is the difference between a shallow copy and a deep copy?

A shallow copy creates a new object but copies each field as it is, so fields that refer to other objects, such as a list, still point at the same objects as the original. A deep copy also copies those referenced objects, recursively, so the copy and the original share nothing mutable.

### What is the difference between == and is in Python?

The is operator checks identity: whether both names refer to the same object. The == operator checks equality by calling __eq__, which compares values when the class defines it and falls back to identity otherwise. Use is for None and for deliberate identity checks, and == for comparing values.

### Why is Integer 127 == 127 true but 128 == 128 false in Java?

Autoboxing uses Integer.valueOf, which returns cached objects for values from -128 to 127, so two boxed 127s are the same object and == is true. Values outside the cache get new objects, so == compares two different references and is false. Compare boxed numbers with equals() or unbox them first.

### How do you deep copy an object in Java?

Write a copy constructor or static factory that copies every mutable field, recursively creating new lists, arrays and nested objects. Overriding clone() to do the same also works, but Object.clone() on its own is shallow. Serialising and deserialising the object makes a deep copy too, but it is slow and needs every class to be Serializable.


---

## Module 11: Exception Handling in OOP

*Original URL: https://codekairo.com/notes/oop/exception-handling*

### Overview

Quick answer

### What is exception handling in object-oriented programming?

Exception handling is the mechanism for reporting and recovering from errors without checking a return code after every call. Code that detects a problem throws (raises) an exception object, the call stack unwinds, and the nearest matching catch or except block handles it. Exceptions are objects in a class hierarchy, so a handler can catch one specific error or a whole family.

- How exceptions work
- try, catch and finally
- Custom exception classes
- Checked and unchecked exceptions in Java
- Exception safety and RAII in C++
- try-with-resources and with
- Best practices
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Things go wrong at run time: a file is missing, an amount is negative, a balance is too low, the network drops. Exception handling separates the code that detects a problem from the code that knows what to do about it , which is often several calls further up. In OOP languages an exception is an ordinary object whose class says what went wrong, and exception classes form hierarchies just like any other classes — so you catch a specific error, or a whole family of them, by type. This note covers the mechanics in C++, Java and Python, Java's checked and unchecked exceptions, custom exception classes, and the techniques that guarantee clean-up: RAII, try -with-resources and with .

### How exceptions work

- Code detects a problem and throws (C++, Java, JavaScript) or raises (Python) an exception object.
- Normal execution stops. The runtime unwinds the call stack : it leaves the current function, then its caller, and so on, running clean-up code — C++ destructors, finally blocks, context-manager exits — on the way.
- The first enclosing handler whose type matches the exception's class (or a parent class) runs, and execution continues after that handler.
- If no handler matches, the program ends: Java and Python print a stack trace or traceback, and C++ calls std::terminate .

### try, catch and finally

Java (since Java 7) and Python can name several types in one handler: a multi-catch in Java, a tuple such as except (KeyError, ValueError) as e: in Python.

Handlers are tried in order , and the first one whose type matches wins, so put the most specific types first. Java refuses to compile a handler for a subclass placed after one for its parent, because it could never run; C++ compilers warn; Python silently runs the first match. In C++, always catch by reference ( const X& ): catching by value copies the exception and slices off any derived part.

A finally block runs whether the try completed, threw, or executed return . One trap: a return inside finally overrides the try block's return value and silently discards any exception in flight.

### Custom exception classes

Define your own exception classes when callers need to tell your errors apart from others, or when an error should carry data. Group them under one base class for your module, so a caller can catch the specific case it can fix and the whole family otherwise:

Every banking failure derives from BankError, unchecked in the Java version because BankError extends RuntimeException. InsufficientFundsError carries the numbers a handler needs. A handler for the parent catches the whole family; one for a child catches only that case.

Inherit from the right root: std::runtime_error (or another std::exception subclass) in C++; Exception for a checked or RuntimeException for an unchecked exception in Java; Exception in Python, never BaseException . End the name in Exception or Error as the language's library does.

The program below uses that hierarchy, most specific handler first. The audit line is clean-up that must happen after every attempt: finally in Java, Python and JavaScript, and in C++ a destructor at the end of the loop body — RAII standing in for finally . Python's else holds the success message, so the try block contains only the call that can fail:

Nothing is raised: the try block finishes, both except clauses are skipped, else prints the success line, finally logs the attempt, and execution carries on.

- Nothing is raised: the try block finishes, both except clauses are skipped, else prints the success line, finally logs the attempt, and execution carries on.
- InsufficientFundsError is raised: the first except clause matches, else is skipped because something was raised, and finally still runs.
- AccountFrozenError is raised: it fails the first except, which wants a different subclass, and matches the second because it is a BankError. finally runs again.
- An exception nobody here handles, such as a TypeError from a bug: no except matches, finally runs anyway, and the exception leaves the statement for the caller to handle.

```
#
include
<iostream>
#
include
<stdexcept>
#
include
<string>
using
namespace
std
;
class
BankError
:
public
runtime_error
{
// base of the family
public
:
using
runtime_error
::
runtime_error
;
}
;
class
InsufficientFundsError
:
public
BankError
{
public
:
const
int
needed
,
available
;
// data a handler can use
InsufficientFundsError
(
int
needed
,
int
available
)
:
BankError
(
"insufficient funds"
)
,
needed
(
needed
)
,
available
(
available
)
{
}
}
;
class
AccountFrozenError
:
public
BankError
{
public
:
explicit
AccountFrozenError
(
const
string
&
id
)
:
BankError
(
"account "
+
id
+
" is frozen"
)
{
}
}
;
class
Account
{
string id
;
int
balance
;
bool
frozen
=
false
;
public
:
Account
(
string id
,
int
balance
)
:
id
(
id
)
,
balance
(
balance
)
{
}
void
freeze
(
)
{
frozen
=
true
;
}
int
withdraw
(
int
amount
)
{
if
(
frozen
)
throw
AccountFrozenError
(
id
)
;
if
(
amount
>
balance
)
throw
InsufficientFundsError
(
amount
,
balance
)
;
return
balance
-=
amount
;
}
}
;
struct
AuditLine
{
// RAII: the destructor runs however the block is left
int
attempt
;
~
AuditLine
(
)
{
cout
<<
"audit: attempt "
<<
attempt
<<
" logged\n"
;
}
}
;
int
main
(
)
{
Account
acct
(
"ACC-7"
,
1000
)
;
int
amounts
[
]
=
{
300
,
5000
,
100
}
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
3
;
i
++
)
{
if
(
i
==
2
)
acct
.
freeze
(
)
;
AuditLine audit
{
i
+
1
}
;
try
{
int
left
=
acct
.
withdraw
(
amounts
[
i
]
)
;
cout
<<
"withdraw "
<<
amounts
[
i
]
<<
": ok, balance "
<<
left
<<
"\n"
;
}
catch
(
const
InsufficientFundsError
&
e
)
{
// most specific first
cout
<<
"withdraw "
<<
amounts
[
i
]
<<
": need "
<<
e
.
needed
<<
", have "
<<
e
.
available
<<
"\n"
;
}
catch
(
const
BankError
&
e
)
{
// the rest of the family
cout
<<
"withdraw "
<<
amounts
[
i
]
<<
": bank error: "
<<
e
.
what
(
)
<<
"\n"
;
}
}
return
0
;
}
```

Output

```
withdraw 300: ok, balance 700
audit: attempt 1 logged
withdraw 5000: need 5000, have 700
audit: attempt 2 logged
withdraw 100: bank error: account ACC-7 is frozen
audit: attempt 3 logged
```

Attempt 1: main calls acct.withdraw(300) inside the try block, and a frame for withdraw goes on top of main's.

- Attempt 1: main calls acct.withdraw(300) inside the try block, and a frame for withdraw goes on top of main's.
- withdraw returns normally with the balance, 700; its frame is popped, the try block prints, and both catch blocks are skipped.
- The finally block runs after the try block too, logging attempt 1. It runs on every path out of the try statement.
- Attempt 2: main calls acct.withdraw(5000) inside the try block, and a frame for withdraw goes on top of main's.
- 5000 is more than the balance of 700, so withdraw throws an InsufficientFundsError carrying both numbers. Normal execution stops at once.
- The runtime unwinds withdraw's frame and tries main's handlers in order. The first, for InsufficientFundsError, matches, and reads needed and available off the object.
- With the exception handled, finally runs and logs attempt 2; then the loop carries on as if nothing had happened.
- Attempt 3: the account has been frozen, and withdraw(100) is called. A new frame for withdraw goes on top of main's.
- withdraw sees the frozen account and throws an AccountFrozenError. Its message names the account; it has no numbers to carry.
- withdraw's frame is unwound. The first handler wants an InsufficientFundsError, which this is not; the second, for BankError, matches because AccountFrozenError is a BankError.
- finally logs attempt 3. Three attempts, three different paths, and the audit line printed after every one.

When you catch one exception and throw another, keep the original as the cause : new BankError("transfer failed", e) in Java (with a matching constructor), raise BankError("transfer failed") from e in Python, std::throw_with_nested in C++. The stack trace then shows both.

### Checked and unchecked exceptions in Java

Everything thrown is a Throwable. RuntimeException, Error and everything under them are unchecked; the rest — 4 of these 14, Exception and IOException among them — are checked, so a method must catch them or declare them with throws.

- Checked exceptions — Exception and its subclasses, except RuntimeException 's branch. A method that can throw one must either catch it or declare it with throws , and the compiler enforces this. Use them for conditions a caller can reasonably recover from: a file that does not exist, a network timeout.
- Unchecked exceptions — RuntimeException , Error and their subclasses. No declaration is needed. They usually signal programming mistakes (a null dereference, an invalid argument), which the fix is to correct, not to catch.

throw raises an exception; throws in a method signature declares which checked exceptions may escape it. An overriding method may not declare broader checked exceptions than the method it overrides. Checked exceptions are a Java feature: C++, Python, C# and Kotlin have none, and many Java libraries now prefer unchecked exceptions because checked ones do not compose well with lambdas.

The other two hierarchies, briefly. C++'s std::exception has logic_error ( invalid_argument , out_of_range ) for bugs and runtime_error for conditions found while running, plus bad_alloc ; C++ can technically throw any type, even an int , but should not. Python's root is BaseException ; SystemExit and KeyboardInterrupt derive from it directly, which is why except Exception: does not swallow Ctrl+C and a bare except: does.

### Exception safety and RAII in C++

C++ has no finally . Instead it guarantees that when a scope is left — normally, by return , or by an exception unwinding through it — the destructors of its local objects run, in reverse order of construction. RAII (Resource Acquisition Is Initialization) builds on that: wrap every resource in an object that acquires it in the constructor and releases it in the destructor. std::unique_ptr frees memory, std::lock_guard releases a mutex and std::ifstream closes a file, whatever path the code takes.

Library designers describe what a function promises if it throws with three exception-safety guarantees :

Destructors must not throw. Since C++11 they are implicitly noexcept , and an exception escaping one during stack unwinding calls std::terminate .

### try-with-resources and with

Java and Python get deterministic clean-up through a language construct instead of destructors. Java's try-with-resources (Java 7) accepts objects implementing AutoCloseable and calls close() on each, in reverse order, when the block ends — before any catch or finally runs. Python's with statement calls a context manager's __exit__ the same way. JavaScript in Node 16 has neither, so nested try / finally does the job. In every version below, both resources are closed in reverse order before the handler sees the exception:

```
#
include
<iostream>
#
include
<stdexcept>
#
include
<string>
using
namespace
std
;
class
Resource
{
// RAII: acquire in the constructor, release in the destructor
string name
;
public
:
explicit
Resource
(
string n
)
:
name
(
n
)
{
cout
<<
"open "
<<
name
<<
"\n"
;
}
~
Resource
(
)
{
cout
<<
"close "
<<
name
<<
"\n"
;
}
}
;
int
main
(
)
{
try
{
Resource
db
(
"db"
)
;
Resource
file
(
"file"
)
;
cout
<<
"working\n"
;
throw
runtime_error
(
"disk full"
)
;
}
catch
(
const
exception
&
e
)
{
// destructors already ran during unwinding
cout
<<
"caught: "
<<
e
.
what
(
)
<<
"\n"
;
}
return
0
;
}
```

Output

```
open db
open file
working
close file
close db
caught: disk full
```

try-with-resources opens db first. A resource is any object implementing AutoCloseable.

- try-with-resources opens db first. A resource is any object implementing AutoCloseable.
- Then file, on top of db. The block works with both, and they will be closed in the reverse of this order.
- The block throws an IllegalStateException. Before any handler is looked at, the block must be left, which means closing what it opened.
- file, opened last, is closed first — exactly as C++ destroys local objects in reverse order of construction.
- Then db. Had close() itself thrown here, Java would keep the original exception and attach the new one as suppressed.
- Only now does the catch block run, with both resources already closed. Python's with statement and C++'s RAII destructors give the same order.

If close() itself throws while another exception is already propagating, Java keeps the original as the main exception and attaches the second with addSuppressed ; you can read it back with getSuppressed() .

### Best practices

- Throw exceptions for exceptional conditions, not for ordinary control flow such as ending a loop.
- Catch only what you can handle, at the level that knows what to do; let the rest propagate.
- Never swallow an exception with an empty handler; at the very least log it with its stack trace.
- Throw specific types, and give messages that name the bad value: "amount -50 must be positive".
- Release resources with RAII, try-with-resources or with , never by hoping a later line runs.
- Validate arguments early and fail fast, so the exception is thrown near the bug rather than far from it.

### Common mistakes

- Catching a parent type before a child type, so the specific handler never runs.
- Catching C++ exceptions by value, which copies and slices them.
- Writing except: or catch (Throwable t) , which also swallows interrupts and fatal errors.
- Putting return in a finally block, which hides the exception that was in flight.
- Letting an exception escape a C++ destructor.
- Wrapping a large block in one try so an unrelated bug is caught by a handler meant for one call.

### Interview questions

What happens when an exception is thrown inside a constructor? The object is never created, so nothing receives a reference to it. In C++ its destructor does not run, but the members and base classes that were already fully constructed are destroyed — which is why owning members should be RAII types rather than raw pointers. In Java and Python the partly built object simply becomes garbage.

Why should C++ destructors not throw? Destructors run during stack unwinding. If one throws while another exception is already propagating, the program has two active exceptions and C++ calls std::terminate . Since C++11 destructors are noexcept by default, so a throw escaping one terminates the program even outside unwinding.

When should you use checked exceptions and when unchecked? Use checked exceptions for conditions a caller can reasonably anticipate and recover from, where forcing them to decide is helpful — a missing file, a failed connection. Use unchecked exceptions for programming errors and violated preconditions, where the right response is fixing the code. Many modern APIs lean towards unchecked exceptions to keep signatures and lambdas simple.

Can you catch multiple exceptions in one block? Yes. Java 7 added multi-catch, which lists the types separated by a vertical bar, as long as none is a subclass of another. Python takes a tuple: except (KeyError, ValueError) as e: . C++ has no direct form; catch a common base class by reference, or write separate handlers.

What are suppressed exceptions in Java? When try-with-resources closes a resource and close() throws while an exception from the try block is already propagating, the closing exception is not allowed to replace the original. It is attached to the original with addSuppressed , and the caller can inspect it with getSuppressed() .

What is the difference between EAFP and LBYL? LBYL — look before you leap — checks conditions first: if key in d: value = d[key] . EAFP — easier to ask forgiveness than permission — tries the operation and handles the exception: try: value = d[key] then except KeyError: . Python favours EAFP, which also avoids races where the condition changes between the check and the use.

Is catching Exception or Throwable a good idea? Only at the outermost level of a program or thread, to log the failure and keep a server running or exit cleanly. Lower down it hides bugs and catches things you cannot handle, such as OutOfMemoryError when catching Throwable , or KeyboardInterrupt with a bare except: in Python.

How does an exception differ from an error code in OOP design? An exception cannot be silently ignored, carries a typed object with data and a stack trace, and passes through intermediate functions without any code in them. An error code is cheaper and explicit in the signature but must be checked after every call. Exceptions suit rare failures; return values, or result and optional types, suit expected outcomes like "not found".

This is the last note in the OOP series. Go back to the Introduction to Object-Oriented Programming for a recap, then take the OOP Intermediate skill test .

### What is the difference between checked and unchecked exceptions in Java?

Checked exceptions, subclasses of Exception other than RuntimeException such as IOException, must be caught or declared with throws, and the compiler enforces it. Unchecked exceptions, RuntimeException and Error and their subclasses such as NullPointerException, need neither. Checked ones signal recoverable conditions; unchecked ones usually signal programming bugs.

### What is the difference between throw and throws in Java?

throw is a statement that actually raises an exception object at that point: throw new IllegalArgumentException("negative"). throws is part of a method declaration that lists the checked exceptions the method may let escape, such as void read() throws IOException, so that callers know to handle them.

### Does the finally block always execute?

It runs whether the try block completes normally, throws, or returns, and even if a catch block throws. It does not run if the process ends first, for example through System.exit in Java, os._exit in Python, a crash, or the process being killed, and it cannot run while the try block loops forever.

### What is RAII in C++?

RAII, Resource Acquisition Is Initialization, ties a resource to an object's lifetime: the constructor acquires the resource and the destructor releases it. Because C++ runs destructors of local objects whenever a scope is left, including during exception unwinding, the resource is always released. std::unique_ptr, std::lock_guard and std::fstream all work this way.

### What is the difference between Error and Exception in Java?

Both extend Throwable. An Exception signals a condition an application might reasonably catch and recover from. An Error, such as OutOfMemoryError or StackOverflowError, signals a serious problem in the runtime that ordinary code should not try to handle. Both Error and RuntimeException are unchecked.

### What does the else block do in a Python try statement?

The else block runs only when the try block finished without raising an exception, and before finally. It lets you keep the try block to just the call that might fail, so a bug in the follow-up code is not accidentally caught by an except clause meant for that call.


---

