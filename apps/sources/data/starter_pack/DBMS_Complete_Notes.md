# Database Management Systems (DBMS)

> **Source**: [CodeKairo CS Notes](https://codekairo.com/notes/dbms)  
> **Overview**: Complete interview and exam preparation notes covering ER models, relational keys, normalization, SQL, transactions, ACID properties, concurrency control, B+ trees, and NoSQL.

---

## Table of Modules

1. [Introduction to DBMS](#module-1-introduction-to-dbms)
2. [ER Model in DBMS](#module-2-er-model-in-dbms)
3. [Keys in DBMS](#module-3-keys-in-dbms)
4. [Functional Dependencies in DBMS](#module-4-functional-dependencies-in-dbms)
5. [Normalization in DBMS: 1NF to BCNF](#module-5-normalization-in-dbms-1nf-to-bcnf)
6. [SQL Basics: DDL, DML, DCL and TCL](#module-6-sql-basics-ddl,-dml,-dcl-and-tcl)
7. [SQL Joins](#module-7-sql-joins)
8. [SQL GROUP BY, HAVING and Subqueries](#module-8-sql-group-by,-having-and-subqueries)
9. [Transactions and ACID Properties in DBMS](#module-9-transactions-and-acid-properties-in-dbms)
10. [Concurrency Control in DBMS](#module-10-concurrency-control-in-dbms)
11. [Indexing and B+ Trees in DBMS](#module-11-indexing-and-b+-trees-in-dbms)
12. [SQL vs NoSQL Databases](#module-12-sql-vs-nosql-databases)

---

## Module 1: Introduction to DBMS

*Original URL: https://codekairo.com/notes/dbms/introduction-to-dbms*

### Overview

Quick answer

### What is a DBMS?

A DBMS (database management system) is software that stores data in a database and lets many users and programs define, query, update and protect it. It takes care of storage, concurrent access, crash recovery, integrity rules and security so that applications do not have to. MySQL, PostgreSQL, Oracle Database, SQL Server and MongoDB are examples.

- What a DBMS does
- DBMS vs file system
- Data models
- The three-schema architecture
- Data independence
- Database users and the DBA
- Types of databases and architectures
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A database is an organized collection of related data: a college's students, courses and marks, or a bank's customers, accounts and transfers. A database management system (DBMS) is the software that stores that data and lets many people and programs use it at the same time without corrupting it. It decides how the bytes sit on disk, answers questions written in a query language such as SQL, enforces the rules the data must follow, and brings the data back to a correct state after a crash. Almost every application you use keeps its state in one.

### What a DBMS does

The definition to say in an interview: a DBMS is a collection of programs that lets users define, create, query, update and administer a database . Behind that sentence sit the services every DBMS provides:

- Data definition : a data definition language (DDL) to describe tables, columns, types and constraints.
- Data manipulation : a data manipulation language (DML) to insert, update, delete and read rows.
- Query processing : an optimizer that turns a declarative query ("what I want") into an efficient plan ("which index, which join order").
- Transaction management : a group of operations happens completely or not at all, even across a crash.
- Concurrency control : many users read and write at once, and each sees a consistent picture.
- Recovery : logs and backups restore the database after a power failure or a lost disk.
- Security and integrity : users get only the access they are granted, and constraints reject invalid data.

A query passes through the query processor (parsed, checked against the data dictionary, planned by the optimizer, run by the executor) and the storage manager (access checked, made part of a transaction, served from the buffer, read from files). The log is what recovery replays after a crash.

Keep three terms apart. The database is the data. The DBMS is the software. The database system is both together with the applications that use them. The DBMS also keeps metadata , data about the data (table definitions, column types, constraints, users and privileges), in a system catalog or data dictionary; in MySQL you can read it through INFORMATION_SCHEMA .

### DBMS vs file system

Before databases, every program kept its records in files of its own format. That arrangement fails in predictable ways, and each failure became a feature of the DBMS.

Each office keeps its own file of the same students. Every name and city is stored in both files, 4 values held twice, and nothing links a row in one file to its twin in the other.

- Each office keeps its own file of the same students. Every name and city is stored in both files, 4 values held twice, and nothing links a row in one file to its twin in the other.
- Asha moves to Mumbai and the accounts office updates its file. The exam cell's copy still says Pune, so the two files now disagree and nothing in either can say which one is right.
- With a DBMS each student is stored once, and the change of city is one UPDATE. Both offices read the same row through their own views, so they cannot disagree, and a new question is a query rather than a new program.

A file system is still the right tool for some jobs: a small single-user tool, logs that are only appended and read in order, or large media files (a database usually stores the video's path, not the video).

### Data models

A data model is the set of concepts used to describe a database's structure: what kinds of things exist, how they relate, and which rules they obey.

A tree gives each record one parent, so DBMS, taken by two students, is stored twice. A network lets the one DBMS record have two parents. The relational model has no links at all: an enrolment is a row of values, and a join matches them.

Models are also grouped by how close they sit to the user. Conceptual models (the ER model) describe data the way people think about it. Representational or logical models (the relational model) describe what the DBMS implements. Physical models describe files, pages and record layouts. The relational model, proposed by E. F. Codd in 1970, became the standard for business data because tables are simple, its query languages are declarative, and its theory of keys, dependencies and normal forms is exact.

### The three-schema architecture

A schema is the description of a database, its design. An instance (or state) is the data stored in it at one moment. The schema changes rarely; the instance changes with every insert. The ANSI/SPARC three-schema architecture describes one database at three levels:

The DBMS keeps two mappings : external/conceptual (how a view is computed from the tables) and conceptual/internal (how each table is stored). There can be many external schemas, but there is exactly one conceptual schema and one internal schema.

### Data independence

Data independence is the payoff of the three levels: the schema at one level can change without changing the schema at the level above, because only the mapping between them changes.

- Physical data independence : change the internal schema without changing the conceptual schema. Adding an index, moving a table to a faster disk, compressing pages or changing the file organization leaves every table and every query untouched.
- Logical data independence : change the conceptual schema without changing the external schemas or the programs written against them. Adding a column or splitting a table leaves applications that read through views working.

One database, described three times: the views each user sees, the tables of the whole database, and the pages and indexes that store them. The DBMS keeps a mapping between each pair of neighbouring levels and translates every query through both.

- One database, described three times: the views each user sees, the tables of the whole database, and the pages and indexes that store them. The DBMS keeps a mapping between each pair of neighbouring levels and translates every query through both.
- Physical data independence: adding an index on email changes the internal level and its mapping only. The student table and both views are untouched, so no query or program changes.
- Logical data independence: fee moves to a table of its own. The accounts view is redefined as a join of student and fees, so it shows the same columns as before, and the programs that read through it keep working.

Logical data independence is harder to achieve. Applications depend on the logical structure (table and column names, which table holds what), while almost nothing depends on how pages are laid out. Every relational DBMS gives you physical independence; logical independence holds only as far as views can hide a change.

### Database users and the DBA

The DBA 's duties are a standard interview list: defining the schema and storage structures, changing them as needs evolve, granting and revoking authorization, planning backups and recovery, monitoring performance and disk space, tuning indexes and queries, and applying upgrades and security patches.

### Types of databases and architectures

The labels overlap: PostgreSQL is relational, centralized by default and mostly used for OLTP, while a warehouse is relational but tuned for OLAP.

Applications reach a database in a one-tier , two-tier (client-server) or three-tier arrangement. Web applications are three-tier, which keeps database credentials and business rules off the user's device.

One tier: the user or app works on the database on the same machine. Two tier: a client sends SQL straight to the database server. Three tier: the client talks only to an application server, which alone holds the database connection and the business rules.

### Common mistakes

- Calling MySQL "a database": it is a DBMS that manages many databases.
- Describing the three levels as three databases: they are three descriptions of one database.
- Swapping the two independences: adding an index is physical, adding a column is logical.
- Using "schema" and "instance" as synonyms: the schema is the design, the instance is today's data.
- Claiming a DBMS is always faster than files: it is safer and more general, but a plain file can be faster for one fixed access pattern.

### Interview questions

What is a DBMS? Name its main functions. A DBMS is software for defining, storing, querying and administering a database. Its main functions are data definition, data manipulation, query optimization, transaction management, concurrency control, recovery, and security with integrity enforcement.

What problems of file-based systems does a DBMS solve? Redundancy and inconsistency, difficulty of answering new questions, data isolated in different formats, integrity rules hidden in code, partial updates after a crash, concurrent programs overwriting each other, and coarse security. Each maps to a DBMS feature: one shared schema, SQL, constraints, transactions, concurrency control and access control.

Explain the three-schema architecture. It describes one database at the internal (physical storage), conceptual (logical structure of the whole database) and external (per-user views) levels. The DBMS maps between adjacent levels, so a change at one level is absorbed by a mapping instead of reaching the users.

What is the difference between physical and logical data independence? Which is harder? Physical independence means changing storage without changing tables; logical independence means changing tables without changing applications or views. Logical independence is harder, because programs depend on table and column names but not on page layouts.

What is the difference between a schema and an instance? The schema is the structure: table names, columns, types and constraints. The instance is the data present at a given moment. The schema is sometimes called the intension and the instance the extension.

What is a data dictionary? It is the system catalog: metadata describing every table, column, type, index, constraint, user and privilege. The DBMS reads it to check and plan every query; in MySQL it is exposed through INFORMATION_SCHEMA .

What are DDL and DML? DDL ( CREATE , ALTER , DROP ) defines the structure, and DML ( SELECT , INSERT , UPDATE , DELETE ) works on the rows. The SQL basics note covers them with DCL and TCL.

What is the difference between two-tier and three-tier architecture? In two-tier, the client connects to the database directly. In three-tier, an application server sits between them, holding business logic and the database connection, which improves security and lets each tier scale on its own.

Next, learn to design a database before building it: ER Model in DBMS . To check the basics, try the SQL (Basic) skill test .

### What is the difference between a database and a DBMS?

A database is the organized collection of related data itself, such as a college's student and course records. A DBMS is the software that creates, stores and manages that data and answers queries on it. The two together, with the applications that use them, make up a database system.

### What is the difference between DBMS and RDBMS?

An RDBMS is a DBMS built on the relational model: data sits in tables of rows and columns, tables are linked by keys, and SQL is the query language. DBMS is the wider term and also covers hierarchical, network, document and other non-relational systems. MySQL and PostgreSQL are RDBMSs; MongoDB is a DBMS but not an RDBMS.

### What are the three levels of DBMS architecture?

The ANSI/SPARC architecture has an internal level (how data is physically stored: files, pages, indexes), a conceptual level (the logical structure of the whole database: tables, relationships, constraints) and an external level (the views each user or application sees). Mappings between the levels give data independence.

### What is data independence in DBMS?

Data independence is the ability to change the schema at one level without changing the level above it. Physical data independence lets you add an index or move files without touching the tables; logical data independence lets you add a column or split a table without rewriting applications that read through views.

### What does a database administrator do?

A DBA is responsible for the whole database system. The DBA defines and changes the schema and storage structures, grants and revokes access, plans backups and recovery, monitors performance and disk space, and applies upgrades. In small teams developers often share these duties.

### Why use a DBMS instead of files?

A file system stores bytes but knows nothing about what they mean. A DBMS removes duplicated and inconsistent data, answers new questions with a query instead of a new program, enforces integrity rules, keeps concurrent users from overwriting each other, recovers after crashes and controls who may see what.


---

## Module 2: ER Model in DBMS

*Original URL: https://codekairo.com/notes/dbms/er-model*

### Overview

Quick answer

### What is the ER model in DBMS?

The entity–relationship (ER) model is a conceptual design model that describes a database as entities (real-world things such as a student or a book), their attributes, and the relationships between them, with cardinality and participation constraints. It is drawn as an ER diagram before any table exists, and fixed rules then turn the diagram into relational tables.

- Entities and entity sets
- Attributes
- Relationships and their degree
- Cardinality and participation
- Weak entities
- Generalization, specialization and aggregation
- Worked example: a library
- Converting an ER diagram to tables
- Common mistakes
- Interview questions
- Common questions
- Test yourself

The entity–relationship (ER) model, introduced by Peter Chen in 1976, is how a database is designed before it is built. You describe the world the database must remember as entities (things), attributes (their properties) and relationships (how things are connected), together with rules such as "every book has exactly one publisher". The result, an ER diagram, is easy to discuss with people who will never write SQL, and it converts into tables by a short list of fixed rules. Interviewers ask both halves: draw or read a diagram, then turn it into tables.

### Entities and entity sets

An entity is a real-world object that can be told apart from all others: the student with roll number 101, the member with card number 5521. An entity set is the set of all entities of the same type: all students, all books. In a diagram an entity set is a rectangle, and it usually becomes one table, with each entity a row.

A strong entity set has a key of its own. A weak entity set does not, and depends on another entity set for its identity (covered below).

### Attributes

Attributes describe an entity. Each has a domain , the set of values it may take. The types interviewers ask about:

An attribute can also be null when the value is unknown or does not apply, such as a member with no email address.

### Chen notation

Rectangles are entity sets and diamonds relationships, doubled for a weak entity and the relationship that identifies it. Ovals are attributes: the key underlined, a partial key dash-underlined, multi-valued doubled, derived dashed, and a composite one split into its parts.

Many tools use crow's foot notation instead, where the line ends show cardinality (a single bar for one, a three-pronged "crow's foot" for many) and a circle or bar shows optional or mandatory participation. The meaning is the same.

### Relationships and their degree

A relationship associates entities: Asha borrows copy 2 of a book. A relationship set is the set of all such associations of one kind, drawn as a diamond. A relationship can have attributes of its own: issue_date belongs to borrows , not to the member or the copy.

The degree of a relationship is the number of entity sets taking part:

A ternary relationship is not the same as three binary ones. Knowing that a supplier supplies a part, that the supplier works for a project, and that the project uses the part does not tell you that this supplier supplies this part to this project.

### Cardinality and participation

Mapping cardinality says how many entities a single entity can be related to through the relationship:

Participation says whether every entity must take part. Total participation (double line) means every entity takes part at least once; it is also called an existence dependency. Partial participation (single line) means some may not. Cardinality is the maximum; participation is the minimum. Some books write both as a pair (min, max), so "a book has (1, 1) publisher" means total participation and at most one.

Each line is one related pair. Cardinality is the most partners one entity has on each side: each department has one head (1:1), a publisher many books but a book one publisher (1:N), authors and books many of each (M:N). A grey entity takes part in no pair, so its side's participation is partial.

### Weak entities

A weak entity set has no attribute set that identifies its entities on its own. A library owns several copies of each book, numbered 1, 2, 3 within that book; "copy 2" is ambiguous until you say which book. So:

- The weak entity set (Copy) is identified through an identifying relationship ( has ) with its owner or identifying entity set (Book).
- Its own distinguishing attribute is a partial key or discriminator ( copy_no ).
- Its full key is the owner's key plus the partial key: ( isbn , copy_no ).
- It always has total participation in the identifying relationship, which is one-to-many from owner to weak entity.

Copy has no key of its own: copy 1 exists for more than one book. It is a weak entity (double box) identified through the double diamond, with total participation (double line), and its key is the owner's isbn plus its partial key copy_no.

If a book is removed, its copies have no meaning left, so the copies' table usually declares ON DELETE CASCADE on its foreign key to the owner.

### Generalization, specialization and aggregation

The extended ER (EER) model adds three ideas for larger designs.

Specialization is top down: split an entity set into subclasses that have extra attributes or relationships. Employee specializes into Engineer (with skill ) and Manager (with budget ). Generalization is bottom up: combine entity sets that share attributes into a superclass, as Car and Truck generalize into Vehicle. Both produce an "is-a" hierarchy, and a subclass inherits all attributes and relationships of its superclass. Two constraints describe the hierarchy:

- Disjoint (an employee is at most one subclass) or overlapping (an employee may be both).
- Total (every employee belongs to some subclass) or partial (some belong to none).

Aggregation treats a relationship, together with its entities, as a higher-level entity so that it can take part in another relationship. Employees work on projects, and a manager monitors each employee-project assignment, not the employee or the project alone. Aggregating works on lets monitors connect Manager to the assignment.

### Worked example: a library

Requirements: publishers publish books, and every book has exactly one publisher. Each book has one or more authors, and an author may write many books. The library holds numbered copies of each book. A member may have several copies on loan at once, and a copy is with at most one member at a time. For members we store a name in two parts, phone numbers (any number of them) and a date of birth; age is shown but never stored.

The entity sets and their attributes:

A publisher publishes many books and every book has exactly one publisher: 1 on the Publisher side, N on the Book side, and a double line because every book must take part.

- A publisher publishes many books and every book has exactly one publisher: 1 on the Publisher side, N on the Book side, and a double line because every book must take part.
- Authors and books are many-to-many (M:N). Every book has at least one author, so the Book side is a double line; an author may have no book in the library yet, so that side is single.
- Copy is weak: a double box, joined to its owner Book by the double diamond has, with total participation. Its partial key copy_no is dash-underlined, because copy 2 means something only for one book.
- A member may hold several copies and a copy is with at most one member: 1:N, partial on both sides. issue_date and due_date describe the loan itself, so they hang off the diamond, not off either entity.
- The finished diagram: five entity sets, four relationships, each key on its entity. Read every line twice, once for cardinality (1, M, N) and once for participation (double or single), before turning it into tables.

Applying the mapping rules gives seven tables:

Each strong entity set becomes a table keyed by its key: publisher, book, author, member. Member's composite name becomes first_name and last_name, its derived age is not stored, and its multi-valued phone waits for a table of its own.

- Each strong entity set becomes a table keyed by its key: publisher, book, author, member. Member's composite name becomes first_name and last_name, its derived age is not stored, and its multi-valued phone waits for a table of its own.
- publishes is 1:N, so the one side's key, publisher_id, goes into book as a foreign key, NOT NULL because every book has a publisher. writes is M:N and becomes its own table, writes, keyed by both foreign keys.
- The weak entity Copy becomes a table keyed by its owner's isbn plus copy_no. borrows is 1:N towards Copy, so member_id and the loan's issue_date and due_date go into copy, nullable because most copies are on the shelf.
- The multi-valued phone becomes member_phone(member_id, phone), one row per number, keyed by both. That makes 7 tables, with every relationship now a foreign key or a table.

Two honest notes on this design. First, foreign keys cannot enforce "every book has at least one author" (total participation on the M:N side); that needs application logic or a trigger. Second, because most copies sit on the shelf, member_id , issue_date and due_date in copy are usually null; a separate loan(isbn, copy_no, member_id, issue_date, due_date) table keyed by ( isbn , copy_no ) is an equally correct mapping that avoids the nulls.

### Converting an ER diagram to tables

For Employee specialized into Engineer and Manager, the three layouts are: a table per entity set, where engineer(emp_id, skill) and manager(emp_id, budget) reference employee(emp_id, name, salary) (always works, needs joins); tables for the subclasses only, each repeating name and salary (only when the specialization is total, and best when it is disjoint); or one employee table with a type column and nullable skill and budget (no joins, many nulls).

A favourite question asks for the minimum number of tables for two strong entity sets E1 and E2 joined by one binary relationship R, with no multi-valued attributes:

### Common mistakes

- Putting the foreign key of a 1:N relationship on the "one" side: it goes on the "many" side, or one row would need many values.
- Storing a multi-valued attribute as a comma-separated column: it breaks first normal form; give it its own table.
- Giving a weak entity's table only its partial key as the primary key: copy_no alone repeats for every book.
- Storing derived attributes such as age: they go stale; compute them.
- Reading cardinality as participation: 1:N limits the maximum; whether every entity must take part is a separate rule.
- Replacing a ternary relationship with three binary ones: the combined fact is lost.

### Interview questions

What is an ER diagram used for? It is a conceptual design of the database, made before tables exist. It captures entities, attributes, relationships and constraints in a form non-programmers can check, and it maps to a relational schema by fixed rules.

What are the types of attributes? Simple and composite, single-valued and multi-valued, stored and derived, plus key attributes. A multi-valued attribute becomes a separate table, a composite one is flattened into its parts, and a derived one is not stored.

What is a weak entity? Give an example. An entity set without a key of its own, identified through its owner by an identifying relationship. A copy of a book, a dependent of an employee, or an instalment of a loan; the key is the owner's key plus the partial key.

What is the difference between total and partial participation? Total means every entity must take part in the relationship (double line), partial means it need not (single line). Total participation on the N side of a 1:N relationship becomes a NOT NULL foreign key.

How do you convert a 1:N and an M:N relationship into tables? For 1:N, add the "one" side's key as a foreign key on the "many" side. For M:N, create a new table with both keys as foreign keys, together forming its primary key, plus any relationship attributes.

What is aggregation in the ER model? Treating a relationship and its entities as one higher-level entity so it can take part in another relationship. It models facts about an association itself, such as a manager monitoring an employee's work on a project.

What is a recursive relationship? A relationship between an entity set and itself, such as Employee manages Employee. The two ends get role names, and in tables it becomes a foreign key referencing the same table, such as manager_id referencing emp_id .

Can a relationship have attributes? Yes. An attribute that describes the association rather than either entity belongs to the relationship, such as the issue date of a loan or the grade in an enrolment. For an M:N relationship it becomes a column of the relationship's table.

Next, the keys that make those tables work: Keys in DBMS . Then test your design reading with the SQL (Basic) skill test .

### What is the difference between an entity and an entity set?

An entity is one distinguishable thing, such as the student with roll number 101. An entity set is the collection of all entities of the same type, such as all students. The entity set is drawn as one rectangle in an ER diagram and usually becomes one table.

### What is a weak entity in DBMS?

A weak entity has no key of its own and can be identified only together with its owner entity, through an identifying relationship. Copy number 3 means something only for a particular book. A weak entity's table takes the owner's key plus its own partial key as the primary key.

### What is the difference between total and partial participation?

Total participation means every entity in the set must take part in the relationship, drawn as a double line: every book must have a publisher. Partial participation means some entities may not take part, drawn as a single line: a library member may have no book on loan.

### What is cardinality in the ER model?

Mapping cardinality says how many entities on one side a single entity on the other side can be related to: one-to-one, one-to-many, many-to-one or many-to-many. It decides where the foreign key goes when the diagram is converted into tables.

### How is a many-to-many relationship converted into tables?

It becomes a separate table whose columns are the primary keys of both entity sets, each a foreign key, plus any attributes of the relationship itself. The two foreign keys together form that table's primary key, so the same pair cannot be stored twice.

### What is the difference between generalization and specialization?

Both build a superclass and subclass hierarchy. Generalization works bottom up, combining entity sets that share attributes, such as Car and Truck into Vehicle. Specialization works top down, splitting one entity set into subgroups with extra attributes, such as Employee into Engineer and Manager.


---

## Module 3: Keys in DBMS

*Original URL: https://codekairo.com/notes/dbms/keys-in-dbms*

### Overview

Quick answer

### What are keys in DBMS?

A key is a set of attributes whose values identify a row in a table or link it to another table. A super key is any set that identifies rows uniquely, a candidate key is a minimal super key, the primary key is the candidate key chosen as the row's identity, and a foreign key refers to a key of another table to link the two.

- The keys at a glance
- Super key and candidate key
- Worked example: which sets are keys?
- Primary, alternate and unique keys
- Foreign keys and composite keys
- Natural and surrogate keys
- Integrity constraints
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A table is only useful if you can point at one row and say "that one". Keys are the columns that let you do it, and the columns that tie one table to another. Interviewers love this topic because the definitions sound alike (super, candidate, primary, alternate) and differ in exactly one word. This note defines each, works through one table to decide which column sets are which, and then covers the integrity constraints that keys make possible.

### The keys at a glance

Two more words you will need in normalization: an attribute that belongs to any candidate key is a prime attribute ; every other attribute is non-prime .

### Super key and candidate key

A super key is any set of attributes that no two rows can share. If {roll_no} is unique, then so is {roll_no, name}, {roll_no, name, batch} and every other set that contains roll_no: adding columns to a unique set keeps it unique. Super keys therefore come in families.

A candidate key is a super key with nothing extra in it: remove any one attribute and it stops being unique. "Minimal" means no proper subset is a super key; it does not mean "fewest columns". A table can have several candidate keys of different sizes.

A key is a rule about every row the table may ever hold, decided from the meaning of the data, not from the rows present today. If today's rows happen to be unique on (name, dept_id), that is a coincidence, not a key.

### Worked example: which sets are keys?

Take a student table with five attributes. The college's rules: every student has a unique roll number and a unique college email; names repeat; a department and a batch hold many students.

So the candidate keys are {roll_no} and {email}. We choose roll_no as the primary key : it is short, never NULL, and never changes, whereas a student may change an email address. Email becomes an alternate key , and we declare it UNIQUE so the DBMS enforces it.

How many super keys are there? A set is a super key exactly when it contains roll_no or email. Of the 2^5 = 32 subsets of the five attributes, 2^3 = 8 contain neither (they are subsets of {name, dept_id, batch}), so there are 32 − 8 = 24 super keys . With a single one-attribute candidate key the count would be 2^4 = 16.

Five attributes make 2^5 = 32 sets, drawn here by size. A set is a super key when its closure is all five attributes: knowing its values fixes the whole row.

- Five attributes make 2^5 = 32 sets, drawn here by size. A set is a super key when its closure is all five attributes: knowing its values fixes the whole row.
- Every set containing roll_no or email determines the row: 24 super keys. The 8 grey sets are the subsets of {name, dept_id, batch}, which never identify a student.
- Candidate keys are the minimal super keys: remove any attribute and they stop identifying rows. Only R and E qualify; RN is a super key, but its N can go.
- The designer picks one candidate key as the primary key: roll_no, short and never changing. email becomes an alternate key, declared UNIQUE. Every candidate key is a super key, but 22 of the 24 super keys are not candidate keys.

### Primary, alternate and unique keys

The primary key is the candidate key the designer picks to identify rows. The DBMS enforces two things on it: uniqueness and NOT NULL (entity integrity). A table has at most one primary key, though it may span several columns. Good primary keys are short, stable and meaningless outside the database; this is why many teams use surrogate keys.

Every other candidate key is an alternate key . Declaring it UNIQUE turns the rule into a constraint. The differences interviewers ask for:

If an InnoDB table has no primary key, InnoDB clusters it on the first UNIQUE index whose columns are all NOT NULL, or failing that on a hidden row id it generates. Declaring a primary key yourself is better.

### Foreign keys and composite keys

A foreign key is a set of columns in one table (the child, or referencing table) whose values must match a primary or unique key in another table (the parent, or referenced table). It is how relationships from the ER model become tables. Facts that surprise people:

- A foreign key may be NULL (meaning "not linked") unless declared NOT NULL.
- It may repeat: many students share dept_id CSE.
- It may refer to its own table: employee.manager_id references employee.emp_id .
- The column names need not match, but the types must be compatible.

student.dept_id is a foreign key referencing department.dept_id. Every value must exist in the parent table; it may repeat, as CSE does for 2 students.

- student.dept_id is a foreign key referencing department.dept_id. Every value must exist in the parent table; it may repeat, as CSE does for 2 students.
- INSERT student 105 with dept_id 'CIV': there is no CIV in department, so referential integrity fails and the DBMS rejects the row. Nothing is stored.
- INSERT the same student with dept_id NULL instead: it is accepted, linked to no department. A foreign key may be NULL unless the column is also declared NOT NULL.

A composite key is any key with more than one column. In an enrolment table neither roll_no nor course_id is unique alone, but each pair appears once, so (roll_no, course_id) is the primary key, and each part is also a foreign key. If a student may repeat a course in a later semester, the key widens to (roll_no, course_id, semester).

{roll_no} alone is not a key: 101 appears on 2 rows. One counterexample is enough to rule a key out.

- {roll_no} alone is not a key: 101 appears on 2 rows. One counterexample is enough to rule a key out.
- {course_id} alone is not a key: CS301 appears on 2 rows. One counterexample is enough to rule a key out.
- {roll_no, course_id} is different on every row, which matches the college's rule that a student takes a course once: the composite primary key. The rows agree with the rule; they could never prove it.

```
CREATE
TABLE
department
(
dept_id
CHAR
(
3
)
PRIMARY
KEY
,
dept_name
VARCHAR
(
50
)
NOT
NULL
UNIQUE
)
;
CREATE
TABLE
student
(
roll_no
INT
PRIMARY
KEY
,
email
VARCHAR
(
100
)
NOT
NULL
UNIQUE
,
name
VARCHAR
(
50
)
NOT
NULL
,
dept_id
CHAR
(
3
)
,
batch
SMALLINT
CHECK
(
batch
BETWEEN
2000
AND
2100
)
,
FOREIGN
KEY
(
dept_id
)
REFERENCES
department
(
dept_id
)
ON
DELETE
SET
NULL
ON
UPDATE
CASCADE
)
;
CREATE
TABLE
enrollment
(
roll_no
INT
,
course_id
CHAR
(
5
)
,
grade
CHAR
(
2
)
,
PRIMARY
KEY
(
roll_no
,
course_id
)
,
FOREIGN
KEY
(
roll_no
)
REFERENCES
student
(
roll_no
)
ON
DELETE
CASCADE
)
;
```

In a full schema enrollment.course_id would reference a course table the same way.

### Natural and surrogate keys

The common practice is a surrogate primary key plus a UNIQUE constraint on the natural key, which gives you stable joins and real-world uniqueness.

### Integrity constraints

Integrity constraints are rules the DBMS checks on every insert, update and delete:

MySQL parsed but ignored CHECK constraints before version 8.0.16; from 8.0.16 it enforces them.

### What happens on delete

Referential integrity can be broken from the child side (the rejected insert above) or from the parent side (deleting a department that students still reference). For the parent side, the foreign key's referential action decides: RESTRICT or NO ACTION, CASCADE, SET NULL, or SET DEFAULT (standard SQL sets the column default; MySQL's InnoDB rejects this action). Suppose department ECE is deleted while students 103 and 104 reference it:

DELETE FROM department WHERE dept_id = 'ECE'. Students 103 and 104 still reference it, so the foreign key's ON DELETE action decides what happens to them.

- DELETE FROM department WHERE dept_id = 'ECE'. Students 103 and 104 still reference it, so the foreign key's ON DELETE action decides what happens to them.
- RESTRICT (and NO ACTION): the delete fails with an error and nothing changes. It is the safe choice wherever losing history by accident would be worse than an error.
- CASCADE: ECE is deleted and so are students 103 and 104, 2 rows removed by one statement. Right for rows that mean nothing without their parent, like enrolments.
- SET NULL: ECE is deleted, and students 103 and 104 keep their rows with dept_id NULL, which needs a nullable column. Right when the child outlives its parent, as a student does a merged department.

ON UPDATE takes the same actions when the parent key value changes; ON UPDATE CASCADE copies a renamed key into every child. With no action written, MySQL uses NO ACTION, which in MySQL is the same as RESTRICT. In standard SQL the two differ slightly: RESTRICT checks at once, while NO ACTION checks at the end of the statement (PostgreSQL can defer it to commit).

Choose by meaning: CASCADE for enrolments, which are meaningless without their student; SET NULL for students, who survive a department being merged away; RESTRICT for financial records, where deleting history by accident is worse than an error.

### Common mistakes

- Calling a candidate key "the key with the fewest columns": minimal means no removable attribute, not smallest.
- Deciding keys from sample rows: rows can disprove a key, never prove one.
- Saying a foreign key must be unique or NOT NULL: it may repeat and may be NULL.
- Saying a unique key allows exactly one NULL everywhere: that is SQL Server's rule, not MySQL's or PostgreSQL's.
- Forgetting that every candidate key is also a super key.
- Using CASCADE everywhere: one delete can silently remove thousands of rows.

### Interview questions

What is the difference between a super key, a candidate key and a primary key? A super key is any uniquely identifying set of attributes. A candidate key is a super key with no removable attribute. The primary key is the candidate key chosen to identify rows, and it cannot be NULL.

Can a table have more than one primary key? No. It has at most one primary key, which may be composite. It can have several candidate keys; the ones not chosen are alternate keys, usually declared UNIQUE.

Can a table have no primary key? SQL allows it, but the table then accepts duplicate rows and nothing can reference it reliably. InnoDB still clusters it, on the first NOT NULL unique index or a hidden generated row id.

What is referential integrity? Every non-NULL foreign key value must match an existing value of the referenced key. The DBMS rejects child rows that break it and applies the foreign key's ON DELETE or ON UPDATE action when a parent row changes.

What is the difference between ON DELETE CASCADE and ON DELETE SET NULL? CASCADE deletes the child rows along with the parent. SET NULL keeps the child rows and sets their foreign key to NULL, which requires the column to be nullable.

What is a prime attribute? An attribute that is part of at least one candidate key. In the student example, roll_no and email are prime and the rest are non-prime; 2NF and 3NF are defined in these terms.

Relation R(A, B, C, D) has candidate key A only. How many super keys does it have? Every subset that contains A is a super key, and there are 2^3 = 8 such subsets. They are A, AB, AC, AD, ABC, ABD, ACD and ABCD.

Why prefer a surrogate key? Why not always? It is short, stable and makes joins cheap, and it does not leak business data into other tables. But it does not stop the same real-world entity being inserted twice, so you keep a UNIQUE constraint on the natural key as well.

Next, the rules that decide which columns determine which: Functional Dependencies in DBMS . Practise keys and constraints in the SQL (Basic) skill test .

### What is the difference between a super key and a candidate key?

A super key is any set of attributes that uniquely identifies every row; it may contain extra attributes. A candidate key is a minimal super key: remove any attribute and it no longer identifies rows. Every candidate key is a super key, but not every super key is a candidate key.

### What is the difference between a primary key and a unique key?

A table has one primary key, and its columns can never be NULL. It can have many unique keys, and in MySQL and PostgreSQL a unique column may hold several NULLs. In MySQL's InnoDB the primary key is also the clustered index that orders the table.

### Can a foreign key be NULL?

Yes, unless the column is also declared NOT NULL. A NULL foreign key means the row is not linked to anything, such as a student not yet assigned to a department. Referential integrity only requires that a non-NULL foreign key value exists in the referenced table.

### What is a composite key?

A composite key is a key made of two or more columns, none of which identifies a row alone. In an enrolment table, a roll number repeats across courses and a course across students, but the pair (roll_no, course_id) is unique, so it is the composite primary key.

### What is a surrogate key?

A surrogate key is an artificial identifier with no business meaning, usually an auto-increment integer or a UUID, used as the primary key instead of a natural key such as an email address. It never changes and is compact, but it does not stop duplicate real-world rows on its own.

### How many super keys does a relation have?

If a relation has n attributes and a single candidate key of one attribute, every set containing that attribute is a super key, so there are 2 to the power n−1. With two single-attribute candidate keys there are 2^n − 2^(n−2), counting sets that contain either.


---

## Module 4: Functional Dependencies in DBMS

*Original URL: https://codekairo.com/notes/dbms/functional-dependencies*

### Overview

Quick answer

### What is a functional dependency in DBMS?

A functional dependency X → Y holds in a relation when any two rows that agree on the attributes X must also agree on the attributes Y; the X values determine the Y values. Roll number determines a student's name, so roll_no → name. Functional dependencies define keys and normal forms, and Armstrong's axioms derive every dependency implied by a given set.

- What a functional dependency is
- Trivial and non-trivial dependencies
- Armstrong's axioms
- Attribute closure
- Finding all candidate keys
- Canonical cover
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A functional dependency (FD) is a rule of the form "if you know this, you know that": a roll number fixes a student's name, a course code fixes its title, a PIN code fixes its post office. Functional dependencies are the mathematics underneath keys and normalization. Every normal form is defined with them, and every "find the candidate keys" or "is this relation in BCNF" question is answered by computing with them. This note covers the definition, Armstrong's axioms, attribute closure, finding all candidate keys and computing a canonical cover, each worked by hand.

### What a functional dependency is

For attribute sets X and Y of a relation R, X → Y ("X functionally determines Y", or "Y is functionally dependent on X") holds if any two rows that have the same values for X also have the same values for Y. X is the determinant (left-hand side) and Y the dependent (right-hand side).

An FD is a rule about every state the table is allowed to be in, which comes from the meaning of the data. An instance can only disprove one:

roll_no → name: the rows that agree on roll_no also agree on name. The rows are consistent with it, and the college's rules say it always holds.

- roll_no → name: the rows that agree on roll_no also agree on name. The rows are consistent with it, and the college's rules say it always holds.
- name → roll_no is not a dependency: rows 1 and 4 agree on name (Asha) but differ on roll_no. One such pair disproves it for good.
- roll_no → grade is not a dependency: rows 1 and 2 agree on roll_no (101) but differ on grade. One such pair disproves it for good.
- No two rows share a (roll_no, course_id) pair, so nothing here can contradict roll_no, course_id → grade. It holds because of the college's rule, not because of these rows.
- course_id → grade holds in these four rows by coincidence. No rule says every student in a course gets the same grade, so the next row may break it: data can only disprove a dependency.

The last test is the trap: the data satisfies course_id → grade, but nothing in the college's rules says every student in a course gets the same grade.

FDs generalize keys. K is a super key of R exactly when K → R, that is, K determines every attribute.

### Trivial and non-trivial dependencies

Trivial FDs hold in every relation, so normal-form definitions only ever test non-trivial ones.

### Armstrong's axioms

Given a set F of FDs, many more follow from it. The set of all FDs implied by F is its closure , written F+. Armstrong's axioms generate F+:

They are sound (they derive only FDs that really hold) and complete (every FD that holds can be derived with them). Four derived rules save time:

Decomposition works on the right side only. From AB → C you cannot conclude A → C or B → C.

Augment X → Y by X to get X → XY, and X → Z by Y to get XY → YZ. The right side of the first is the left side of the second, so transitivity gives X → YZ: the union rule, built from the three axioms alone.

- Augment X → Y by X to get X → XY, and X → Z by Y to get XY → YZ. The right side of the first is the left side of the second, so transitivity gives X → YZ: the union rule, built from the three axioms alone.
- Decomposition splits a right side, never a left one. These two rows satisfy AB → C, because no two rows share A and B, yet they break A → C: the same a1 gives c1 and c2.

### Attribute closure

Computing F+ directly is exponential, so in practice you compute the closure of an attribute set , X+: everything X determines.

- Set result = X.
- For each FD Y → Z in F: if Y is entirely inside result, add Z to result.
- Repeat step 2 until a full pass adds nothing.

Take R(A, B, C, G, H, I) with F = {A → B, A → C, CG → H, CG → I, B → H}, and compute (AG)+:

Start with the set itself: (AG)+ begins as {A, G}. Then go down F again and again; a dependency fires when its whole left side is already inside the set, and adds its right side.

- Start with the set itself: (AG)+ begins as {A, G}. Then go down F again and again; a dependency fires when its whole left side is already inside the set, and adds its right side.
- A → B fires because A is inside: add B. The set is now {A, B, G}.
- A → C fires because A is inside: add C. The set is now {A, B, C, G}.
- CG → H fires because C and G are both inside: add H. The set is now {A, B, C, G, H}.
- CG → I fires because C and G are both inside: add I. The set is now {A, B, C, G, H, I}.
- B → H could fire, but H is already in the set, so it adds nothing new.
- A second pass changes nothing, so the loop stops: (AG)+ = ABCGHI, every attribute, so AG is a super key. Neither part is: A+ = ABCH and G+ = G, so AG is a candidate key.

(AG)+ = ABCGHI, every attribute, so AG is a super key. Closure answers three questions:

- Is X a super key? Yes if X+ contains all of R.
- Does F imply X → Y? Yes if Y ⊆ X+. Does F imply B → C? B+ = {B, H}, which lacks C, so no.
- Is X a candidate key? X+ is everything and no proper subset's closure is. Here A+ = {A, B, C, H} (A → B, A → C, B → H; CG → H cannot fire without G) and G+ = {G}, so AG is a candidate key.

### Finding all candidate keys

A method that never misses a key:

- Sort the attributes. Left-only attributes (on some left side, no right side) and attributes that appear in no FD at all cannot be derived, so they belong to every key. Right-only attributes can always be derived from the rest, so they belong to no candidate key. The rest appear on both sides.
- Compute the closure of the must-have set. If it covers R, it is the one and only candidate key.
- Otherwise add "both" attributes to it, one at a time, then two at a time, and so on, keeping every set whose closure is R and skipping any set that contains a key already found.

Example 1. In the relation above, left-only attributes are A and G, right-only are H and I, and B and C appear on both sides. (AG)+ is everything, so AG is the only candidate key .

Example 2. R(A, B, C, D, E) with F = {A → BC, CD → E, B → D, E → A}. Every attribute appears on both sides, so no attribute is forced and we test sets by size.

Pairs containing A or E are not minimal, so only BC, BD and CD needed testing. The only triple without A or E is BCD, which contains BC. The candidate keys are A, E, BC and CD , so every attribute here is prime. That fact matters in the next note: this relation is in 3NF, but B → D has a determinant that is not a super key, so it is not in BCNF.

Every attribute appears on both sides of some dependency, so none is forced into the key and none is ruled out. Test sets by size: A+ = ABCDE, B+ = BD, C+ = C, D+ = D, E+ = ABCDE. A and E reach everything.

- Every attribute appears on both sides of some dependency, so none is forced into the key and none is ruled out. Test sets by size: A+ = ABCDE, B+ = BD, C+ = C, D+ = D, E+ = ABCDE. A and E reach everything.
- A pair containing A or E holds a key already, so it cannot be minimal and is skipped (dashed). Of the other three, BC and CD reach everything and BD does not.
- Every triple contains a key found already — the only one without A or E, BCD, contains BC — so the search stops. The candidate keys are A, E, BC, CD, and every attribute is prime.

### Canonical cover

Two FD sets F and G are equivalent when F+ = G+: each FD of one follows from the other (check with closures). A canonical cover Fc is the simplest set equivalent to F, which makes integrity checks cheap. Removing from a dependency an attribute that does not change F+ is called removing an extraneous attribute.

- Split every right side into single attributes (decomposition).
- For each FD with two or more attributes on the left, test each left attribute: in XA → B, A is extraneous if B ∈ X+ computed with all of F. Drop it if so.
- For each FD X → B, compute X+ using F without that FD. If B is still in it, the FD is redundant; delete it.
- Combine FDs with the same left side (union).

The set after step 3 is a minimal cover ; step 4 makes it the canonical cover. Work F = {A → B, AB → C, C → D, A → D} on R(A, B, C, D):

Start from F. Every right side is already a single attribute, so step 1 changes nothing. Step 2 looks for extraneous attributes on left sides; only AB → C has two.

- Start from F. Every right side is already a single attribute, so step 1 changes nothing. Step 2 looks for extraneous attributes on left sides; only AB → C has two.
- Is A extraneous in AB → C? Without it the left side is B, and B+ under all of F is only B, which lacks C. A stays.
- Is B extraneous in AB → C? Without it the left side is A, and A+ under all of F is ABCD, which contains C. So B is extraneous: AB → C becomes A → C.
- Is A → B redundant? Without it, A+ is only ACD, with no B. Nothing else implies it, so it stays.
- Is A → C redundant? Without it, A+ is only ABD, with no C. Nothing else implies it, so it stays.
- Is C → D redundant? Without it, C+ is only C, with no D. Nothing else implies it, so it stays.
- Is A → D redundant? Without it, A+ is still ABCD, which contains D, so the other dependencies imply it. Delete it.
- The minimal cover is A → B, A → C, C → D. Joining the two with left side A gives the canonical cover {A → BC, C → D}, and A+ = ABCD under it confirms every original dependency still follows.

Minimal cover: {A → B, A → C, C → D}. Canonical cover: {A → BC, C → D} . To confirm equivalence, check each original FD under the cover: A+ = ABCD, so A → B, A → D and AB → C all follow, and C → D is in it.

A minimal cover is not always unique; the order in which you test can give different, equally valid answers.

### Common mistakes

- Splitting a left side: AB → C does not give A → C.
- Treating sample rows as proof of an FD: they can only disprove one.
- Stopping the closure loop after one pass: a later FD can enable an earlier one; repeat until nothing changes.
- Calling any super key a candidate key without checking that its proper subsets are not super keys.
- Testing an extraneous left attribute against F minus the FD itself: left-side tests use all of F; redundancy tests drop the FD.
- Forgetting attributes that appear in no FD: they must be part of every key.

### Interview questions

Define a functional dependency. X → Y holds in R if any two tuples that agree on X also agree on Y. It is a constraint on all legal instances of R, decided from the meaning of the data.

State Armstrong's axioms and say why they matter. Reflexivity, augmentation and transitivity. They are sound and complete, so every implied dependency can be derived with them and nothing false can.

Prove the union rule. From X → Y, augmenting by X gives X → XY. From X → Z, augmenting by Y gives XY → YZ. Transitivity on the two gives X → YZ.

How do you check whether a set of attributes is a super key? Compute its closure under F. It is a super key if the closure is every attribute of the relation, and a candidate key if additionally no proper subset has that property.

R(A, B, C, D) has F = {AB → C, C → D, D → A}. What are the candidate keys? B is left-only and must be in every key, but B+ = {B}. AB+ = ABCD, CB+ = BCDA and DB+ = BDAC, so the keys are AB, BC and BD.

What is the difference between a minimal cover and a canonical cover? Both have no redundant FDs and no extraneous attributes. A minimal cover has single attributes on every right side; a canonical cover merges FDs with the same left side into one.

What is an extraneous attribute? An attribute that can be removed from a dependency without changing the closure of the set. In AB → C with A → C also implied, B is extraneous on the left.

Why do we compute attribute closure instead of F+? F+ can have exponentially many dependencies. Every practical question (is X a key, does F imply X → Y) is answered by one attribute closure, which takes time polynomial in the size of F.

Next, use these tools to design good tables: Normalization in DBMS: 1NF to BCNF . Dependencies and keys are examined in the SQL (Intermediate) skill test .

### What is a trivial functional dependency?

A functional dependency X → Y is trivial when Y is a subset of X, such as {roll_no, name} → name. It holds in every relation and says nothing about the data. It is non-trivial when Y has at least one attribute not in X, and completely non-trivial when X and Y share no attributes.

### What are Armstrong's axioms?

Three inference rules for functional dependencies: reflexivity (if Y is a subset of X, then X → Y), augmentation (if X → Y, then XZ → YZ) and transitivity (if X → Y and Y → Z, then X → Z). They are sound, deriving only valid dependencies, and complete, deriving all of them.

### What is the closure of an attribute set?

The closure X+ is the set of all attributes that X functionally determines under a set of dependencies F. Start with X and keep adding the right side of any dependency whose left side is already inside the set, until nothing changes. If X+ contains every attribute, X is a super key.

### How do you find candidate keys from functional dependencies?

Attributes that appear on no right-hand side must be in every key, and attributes that appear only on right-hand sides are in none. Compute the closure of the must-have set; if it covers all attributes, it is the only key. Otherwise add the remaining attributes in growing combinations and keep the minimal sets whose closure is everything.

### What is a canonical cover?

A canonical cover of F is a simplest equivalent set of dependencies: no dependency is redundant, no attribute on either side is extraneous, and dependencies with the same left side are combined. It implies exactly the same dependencies as F, so checking it on updates is cheaper.

### Can sample data prove a functional dependency?

No. A dependency is a rule about every legal state of the relation. A single pair of rows that agree on X but differ on Y disproves X → Y, but rows that happen to satisfy it prove nothing, because a later insert may break it.


---

## Module 5: Normalization in DBMS: 1NF to BCNF

*Original URL: https://codekairo.com/notes/dbms/normalization*

### Overview

Quick answer

### What is normalization in DBMS?

Normalization is the process of splitting a table into smaller tables, guided by functional dependencies, so that each fact is stored once. It removes insertion, update and deletion anomalies. Each normal form forbids one kind of dependency: 2NF forbids partial dependencies on a key, 3NF transitive ones, and BCNF any dependency whose determinant is not a super key. Every split must be lossless.

- The running example and its anomalies
- The normal forms at a glance
- First normal form (1NF)
- Second normal form (2NF)
- Third normal form (3NF)
- Boyce–Codd normal form (BCNF)
- Lossless join and dependency preservation
- Fourth normal form, briefly
- When to denormalize
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Normalization is the design discipline of storing each fact exactly once. A table that mixes facts about several things (students, departments, courses) repeats some facts on many rows, and repetition invites contradictions. Normalization splits such a table into smaller ones, using the functional dependencies among its columns, until every dependency is "a key determines a fact about that key". This note takes one table through 1NF, 2NF, 3NF and BCNF, checks that every split is lossless, and ends with 4NF and when to denormalize.

### The running example and its anomalies

A college keeps its enrolment sheet like this, one row per student with a list of courses:

The rules of the college, as functional dependencies:

Flattened to one row per student and course, the sheet becomes one wide table, R:

Candidate keys. roll_no appears on no right-hand side, so it is in every key, but its closure is only {roll_no, name, dept, hod}. Adding course_id gives everything (FD4, FD3); adding instructor also gives everything (FD5 brings course_id). name, dept, hod, course_title and grade appear only on right-hand sides, so they are in no key. The candidate keys are {roll_no, course_id} and {roll_no, instructor} ; the prime attributes are roll_no, course_id and instructor.

The repetition causes three anomalies , each visible on these four rows:

Update anomaly: the fact "Dr. Rao heads CSE" is stored on 3 rows, one per CSE enrolment, so a new head means changing all 3 of them.

- Update anomaly: the fact "Dr. Rao heads CSE" is stored on 3 rows, one per CSE enrolment, so a new head means changing all 3 of them.
- Miss one of them and the table contradicts itself: CSE now has two heads, Dr. Das and Dr. Rao, and nothing says which is right. dept → hod is broken by the table's own rows.
- Insertion anomaly: a new course, CS303, cannot be recorded until someone enrols. Its row would need roll_no, which is part of every candidate key and so cannot be NULL.
- Deletion anomaly: when Meera leaves and her row is deleted, the only record that Dr. Iyer heads ECE goes with it. One delete removed two facts.

### The normal forms at a glance

Each form includes the ones above it: every BCNF relation is in 3NF, every 3NF relation in 2NF.

Every BCNF table is in 3NF, every 3NF table in 2NF, and so on. R is only in 1NF, the 2NF Student is stopped by dept → hod, Enrollment by instructor → course_id, and the textbook table by its multivalued dependency. The five final tables reach 4NF.

### First normal form (1NF)

A relation is in 1NF when every attribute holds a single, indivisible value: no lists, no repeating groups such as course1, course2, course3, and no nested tables. The sheet above breaks 1NF, because one cell holds several courses. Flattening it to one row per (student, course) gives R, which is in 1NF. Atomicity is judged by how the data is used: a full name stored in one column is fine if you never query its parts.

### Second normal form (2NF)

A relation is in 2NF when it is in 1NF and no non-prime attribute is partially dependent on a candidate key, that is, dependent on a proper subset of it. Only composite keys can cause this, so a 1NF table whose candidate keys are all single attributes is automatically in 2NF.

R has three partial dependencies: roll_no → name, dept, hod (roll_no is part of both keys), course_id → course_title (part of {roll_no, course_id}), and instructor → course_title through FD5 (part of {roll_no, instructor}). Move each group into a table keyed by its determinant:

Student keeps three rows and Course two, so CS303 can now be added before anyone enrols; Enrollment keeps all four. In Enrollment the only non-prime attribute is grade, and it depends on whole keys, so all three tables are in 2NF.

### Third normal form (3NF)

A relation is in 3NF when, for every non-trivial dependency X → A, either X is a super key or A is a prime attribute. Equivalently: it is in 2NF and no non-prime attribute is transitively dependent on a key through another non-key attribute.

Student breaks 3NF: roll_no → dept and dept → hod, where dept is not a super key and hod is not prime. That is why the CSE head was repeated. Split on dept → hod:

Enrollment is already in 3NF. Its one dependency without a super-key determinant is instructor → course_id, and course_id is prime (it belongs to the key {roll_no, course_id}), which 3NF allows. The 3NF design is Student, Department, Course and Enrollment.

### Boyce–Codd normal form (BCNF)

A relation is in BCNF when, for every non-trivial dependency X → A, X is a super key. No exception for prime attributes.

Enrollment breaks BCNF: instructor → course_id, and instructor alone is not a super key. The redundancy is visible: "Sen teaches CS301" is stored on two rows. Split on the offending dependency, X → A becomes one table (X, A), and the original loses A:

The BCNF design has five tables: Student, Department, Course, Teaches and Enrollment. Every determinant in every table is now a key. The whole decomposition, replayed with the dependency that forced each split:

R is in 1NF: one row per student and course. Its candidate keys are {roll_no, course_id} and {roll_no, instructor}, so roll_no, course_id and instructor are prime and every other column is not. Bold underlined columns are a key.

- R is in 1NF: one row per student and course. Its candidate keys are {roll_no, course_id} and {roll_no, instructor}, so roll_no, course_id and instructor are prime and every other column is not. Bold underlined columns are a key.
- 2NF: roll_no → name, dept, hod breaks it, a partial dependency (roll_no is only part of a key). Split Student off R; the common column roll_no is Student's key, so the join back is lossless.
- 2NF: course_id → course_title breaks it, a partial dependency (course_id is only part of a key). Split Course off rest of R; the common column course_id is Course's key, so the join back is lossless.
- 3NF: dept → hod breaks it, a transitive dependency (dept is not a key and hod is not prime). Split Department off Student; the common column dept is Department's key, so the join back is lossless. The head of CSE, stored 3 times in R, is now stored once.
- BCNF: instructor → course_id breaks it, a determinant that is not a super key (instructor is not a super key of Enrollment). Split Teaches off Enrollment; the common column instructor is Teaches's key, so the join back is lossless. Sen teaching CS301 is now one row, not two.
- Every determinant is now a key: five tables in BCNF. The price is FD4: (roll_no, course_id) → instructor, grade spans Teaches and Enrollment, so no single table can check it any more.

A relation can be in 3NF but not BCNF only if it has two or more candidate keys that overlap, as {roll_no, course_id} and {roll_no, instructor} do here. That is the quick answer when an interviewer asks why 3NF is "usually enough".

### Lossless join and dependency preservation

Every decomposition must be lossless : joining the pieces back must give exactly the original rows. For a split of R into R1 and R2 the test is that the common attributes R1 ∩ R2 are a super key of R1 or of R2.

All four splits above pass it: each time the common column (roll_no, course_id, dept, then instructor) is the key of the table split off, as the decomposition's last line shows at every step.

A lossy split, for contrast: break the enrolment facts (roll_no, course_id, grade) into (roll_no, grade) and (course_id, grade). The common attribute grade determines nothing, and the join back on grade returns six rows instead of four:

Split the 4 enrolment facts into (roll_no, grade) and (course_id, grade). The only common column is grade, and grade determines nothing: A and B each appear on several rows of both pieces.

- Split the 4 enrolment facts into (roll_no, grade) and (course_id, grade). The only common column is grade, and grade determines nothing: A and B each appear on several rows of both pieces.
- Joining the pieces back on grade pairs every roll number with every course of the same grade: 6 rows instead of 4. (101, CS301, B) and (103, CS302, B) never happened, and nothing marks them as false.

A lossy join adds rows rather than dropping them; the information lost is which rows are true.

A decomposition is dependency preserving if every original dependency can be checked inside a single table, without joins. The 2NF and 3NF steps preserve all five dependencies. The BCNF step does not: FD4, (roll_no, course_id) → instructor, grade, now spans Teaches and Enrollment, so an insert can break it unnoticed:

In BCNF, Teaches says which course each instructor teaches and Enrollment which instructor's section each student is in. FD4, a student takes a course once, is in neither table.

- In BCNF, Teaches says which course each instructor teaches and Enrollment which instructor's section each student is in. FD4, a student takes a course once, is in neither table.
- INSERT (101, Gupta, C) into Enrollment. Its key (roll_no, instructor) is new, so the table accepts it, and Teaches is not involved at all.
- Only a join shows the damage: Gupta teaches CS301, so student 101 is now in CS301 twice, with grades A and C. FD4 is broken, and enforcing it needs that join or a trigger on every insert.

This trade-off is a theorem, not a flaw of this example: a lossless BCNF decomposition always exists but may not preserve dependencies, while 3NF synthesis always gives one that is both lossless and dependency preserving. Many designers stop at 3NF when they meet it. A practical middle way is to keep the 3NF Enrollment(roll_no, course_id, instructor, grade) and add a composite foreign key (instructor, course_id) referencing Teaches, so both rules are enforced by constraints.

### Fourth normal form, briefly

A multivalued dependency X ↠ Y says that the set of Y values for an X value is independent of the other attributes. Suppose a separate table lists each course's recommended textbooks and its lab days, which have nothing to do with each other:

The only key is all three columns and there are no non-trivial functional dependencies, so the table is in BCNF. Yet adding a third textbook needs two new rows, one per lab day. course_id ↠ textbook and course_id ↠ lab_day hold with course_id not a super key, so it breaks 4NF . Split it into (course_id, textbook) and (course_id, lab_day), which is lossless. Fifth normal form deals with join dependencies that are not implied by keys, and rarely comes up in practice.

### When to denormalize

Normalization optimizes for correct writes; every split adds a join to some read. Denormalization deliberately reintroduces redundancy where reads dominate:

- Reporting and analytics, where data warehouses use star schemas with wide, repeated dimension columns.
- Derived values read constantly: an order's total, a post's like count, a user's solved count.
- Hot pages where a join on every request costs more than keeping a copy in sync.

The price is the anomalies you removed: the copy must be updated in the same transaction, by a trigger, or by a job that tolerates brief staleness. Normalize first, measure, then denormalize the specific paths that need it.

### Common mistakes

- Defining 2NF with the primary key only: partial dependencies on any candidate key count.
- Calling Enrollment "not in 3NF" because of instructor → course_id: course_id is prime, so 3NF allows it; only BCNF forbids it.
- Splitting on a dependency without checking the join is lossless: the common columns must be a key of one side.
- Assuming BCNF is always the goal: it can cost dependency preservation.
- Thinking a lossy join loses rows: it produces extra, spurious rows.
- Normalizing "for performance": normalization improves integrity; it often makes reads slower.

### Interview questions

Why do we normalize a database? To remove redundancy and the insertion, update and deletion anomalies it causes. Each fact is stored once, so it can be changed in one place and cannot contradict itself.

Explain 1NF, 2NF and 3NF with an example. 1NF: atomic values, one course per row. 2NF: no non-key attribute depends on part of a composite key, so course_title moves to Course. 3NF: no non-key attribute depends on another non-key attribute, so hod moves from Student to Department.

What is the difference between 3NF and BCNF? Give a relation in 3NF but not BCNF. BCNF requires every determinant to be a super key; 3NF also allows a dependency whose right side is prime. Enrollment(roll_no, course_id, instructor, grade) with instructor → course_id is in 3NF but not BCNF.

How do you test whether a decomposition is lossless? For two pieces, check that their common attributes functionally determine all of one piece, that is, form a super key of R1 or of R2. If neither holds, the natural join can create spurious rows.

What is dependency preservation and why does it matter? Every original dependency can be checked within one decomposed table. If one is lost, enforcing it needs a join on every insert or update, which is expensive, so the rule usually goes unenforced.

Is a relation with only two attributes always in BCNF? Yes. Any non-trivial dependency between two attributes A → B makes A a super key, because A then determines both attributes.

What is a multivalued dependency? Which normal form handles it? X ↠ Y means the set of Y values for each X is independent of the remaining attributes, as with a course's textbooks and its lab days. 4NF requires the determinant of every non-trivial multivalued dependency to be a super key.

When would you not normalize fully? When read performance on a measured hot path needs fewer joins, in data warehouses, or when BCNF would lose a dependency you must enforce. The redundancy is then maintained deliberately.

Next, write the tables you designed in SQL: SQL Basics: DDL, DML, DCL and TCL . Normal forms are examined in the SQL (Intermediate) skill test .

### What is the difference between 3NF and BCNF?

3NF allows a non-trivial dependency X → A if X is a super key or A is a prime attribute (part of some candidate key). BCNF drops the second escape: X must always be a super key. BCNF is stricter, and a relation can be in 3NF but not BCNF only when it has overlapping candidate keys.

### What is a partial dependency?

A partial dependency is a non-prime attribute that depends on only part of a composite candidate key. With key (roll_no, course_id), the dependency course_id → course_title is partial. Second normal form removes partial dependencies by moving such attributes into a table keyed by the part they depend on.

### What is a transitive dependency?

A transitive dependency is a non-prime attribute that depends on the key through another non-key attribute: roll_no → dept and dept → hod, so hod depends on roll_no only via dept. Third normal form removes it by moving dept and hod into a separate department table.

### What is a lossless join decomposition?

Splitting R into R1 and R2 is lossless if joining them back always gives exactly R, with no extra rows. The test: the common attributes must be a super key of R1 or of R2. A lossy split creates spurious rows on the join, so you can no longer tell real facts from false ones.

### Is BCNF always dependency preserving?

No. A lossless BCNF decomposition always exists, but it may lose a dependency, so that the rule can only be checked by joining tables. 3NF synthesis always gives a decomposition that is both lossless and dependency preserving, which is why designers sometimes stop at 3NF.

### When should you denormalize a database?

Denormalize when measured read performance matters more than write simplicity: reporting tables, data warehouses with star schemas, stored totals such as an order's amount, or counters shown on every page. Normalize first, then add redundancy deliberately, with a plan to keep the copies consistent.


---

## Module 6: SQL Basics: DDL, DML, DCL and TCL

*Original URL: https://codekairo.com/notes/dbms/sql-basics*

### Overview

Quick answer

### What are DDL, DML, DCL and TCL in SQL?

SQL commands fall into groups. DDL (CREATE, ALTER, DROP, TRUNCATE) defines and changes the structure of tables. DML (INSERT, UPDATE, DELETE, and SELECT, sometimes listed separately as DQL) works on the rows. DCL (GRANT, REVOKE) controls who may do what. TCL (COMMIT, ROLLBACK, SAVEPOINT) groups statements into transactions that succeed or fail together.

- SQL command categories
- DDL: creating and changing tables
- Constraints
- DML: inserting, updating and deleting
- DELETE vs TRUNCATE vs DROP
- SELECT: reading rows
- NULL and three-valued logic
- Pattern matching with LIKE
- DCL and TCL
- Common mistakes
- Interview questions
- Common questions
- Test yourself

SQL (Structured Query Language) is the standard language of relational databases. You use it to define tables, put rows into them, ask questions of them, decide who may touch them, and group changes into transactions. It is declarative : you describe the result you want, and the DBMS's optimizer decides how to get it. The core is standardized (ISO/IEC 9075), and every product adds its own extensions; the examples here run on MySQL 8, and the places where MySQL differs from standard SQL are pointed out.

### SQL command categories

DDL defines structure. CREATE TABLE writes the table's definition into the catalog; there are no rows yet. In MySQL a DDL statement also commits any open transaction.

- DDL defines structure. CREATE TABLE writes the table's definition into the catalog; there are no rows yet. In MySQL a DDL statement also commits any open transaction.
- DML changes the rows. INSERT adds two accounts; the structure is untouched. With autocommit on, as MySQL has by default, each statement is its own transaction.
- DCL controls who may do what. GRANT records a privilege for the user intern: it may read accounts and nothing else. The table and its rows do not change.
- TCL groups statements. START TRANSACTION opens a transaction, and the UPDATE that follows changes account 1 only inside it: under MySQL's default isolation level, other sessions still read 5000.
- The second UPDATE moves the money into account 2, still inside the transaction. Halfway through, a ROLLBACK here would undo both changes at once.
- COMMIT makes both changes permanent together. The total is unchanged, so no money was created or lost; a crash before COMMIT would have kept neither.
- DQL reads. SELECT returns the committed rows as a result and changes nothing, which is why some books list it apart from DML.

Two practical points. MySQL runs in autocommit mode by default, so each statement is its own transaction unless you begin one explicitly. And in MySQL (and Oracle) a DDL statement causes an implicit commit : a CREATE or TRUNCATE in the middle of a transaction commits the work before it and cannot itself be rolled back. PostgreSQL, by contrast, can roll back most DDL.

### DDL: creating and changing tables

```
CREATE
TABLE
departments
(
dept_id
CHAR
(
3
)
PRIMARY
KEY
,
dept_name
VARCHAR
(
50
)
NOT
NULL
UNIQUE
)
;
CREATE
TABLE
students
(
id
INT
PRIMARY
KEY
AUTO_INCREMENT
,
name
VARCHAR
(
50
)
NOT
NULL
,
dept
CHAR
(
3
)
NOT
NULL
,
marks
INT
CHECK
(
marks
BETWEEN
0
AND
100
)
,
city
VARCHAR
(
30
)
DEFAULT
'Pune'
,
FOREIGN
KEY
(
dept
)
REFERENCES
departments
(
dept_id
)
)
;
```

AUTO_INCREMENT is MySQL's way of generating ids; standard SQL (and PostgreSQL) writes GENERATED ALWAYS AS IDENTITY . ALTER TABLE changes an existing table:

```
ALTER
TABLE
students
ADD
COLUMN
email
VARCHAR
(
100
)
UNIQUE
;
ALTER
TABLE
students
MODIFY
COLUMN
city
VARCHAR
(
50
)
DEFAULT
'Pune'
;
-- MySQL syntax
ALTER
TABLE
students
RENAME
COLUMN
city
TO
home_city
;
-- MySQL 8.0+
ALTER
TABLE
students
DROP
COLUMN
email
;
DROP
TABLE
IF
EXISTS
old_results
;
```

MODIFY COLUMN is MySQL's form; standard SQL and PostgreSQL use ALTER COLUMN … TYPE and ALTER COLUMN … SET DEFAULT .

### Constraints

Constraints are rules declared with the table and checked by the DBMS on every change:

MySQL enforces CHECK constraints from version 8.0.16; older versions parsed them and silently ignored them. The keys note covers primary and foreign keys and what ON DELETE CASCADE does.

### DML: inserting, updating and deleting

```
INSERT
INTO
students
(
name
,
dept
,
marks
,
city
)
VALUES
(
'Asha'
,
'CSE'
,
91
,
'Pune'
)
,
(
'Vikram'
,
'CSE'
,
78
,
'Delhi'
)
,
(
'Meera'
,
'ECE'
,
85
,
'Chennai'
)
,
(
'Rohan'
,
'ME'
,
NULL
,
'Pune'
)
,
(
'Priya'
,
'ECE'
,
67
,
'Delhi'
)
;
UPDATE
students
SET
marks
=
marks
+
2
WHERE
dept
=
'ECE'
;
DELETE
FROM
students
WHERE
marks
IS
NULL
;
```

An UPDATE or DELETE without WHERE changes every row. MySQL's client offers a safe-updates mode that refuses such statements, and running them inside a transaction you can roll back is a good habit.

### DELETE vs TRUNCATE vs DROP

DELETE removes the rows its WHERE picks (Rohan, in red) and keeps counting ids from 6. TRUNCATE empties the table but keeps its structure, and the counter restarts at 1. DROP removes the table itself.

### SELECT: reading rows

After the inserts above (before the update and delete), students holds:

```
SELECT
name
,
marks
FROM
students
WHERE
dept
=
'CSE'
ORDER
BY
marks
DESC
;
```

WHERE filters rows, ORDER BY sorts them (ascending by default), and without ORDER BY the order of rows is not guaranteed at all. DISTINCT removes duplicate result rows, and LIMIT cuts the result:

```
SELECT
DISTINCT
city
FROM
students
ORDER
BY
city
;
-- Chennai, Delhi, Pune
SELECT
name
,
marks
FROM
students
ORDER
BY
marks
DESC
LIMIT
2
;
-- top two
SELECT
name
,
marks
FROM
students
ORDER
BY
marks
DESC
LIMIT
2
OFFSET
2
;
-- next two
```

Rohan's NULL comes last here because MySQL sorts NULL as the smallest value: first in ascending order, last in descending. PostgreSQL does the opposite (NULLs sort as largest) and lets you write NULLS FIRST or NULLS LAST . LIMIT is MySQL and PostgreSQL syntax; standard SQL writes FETCH FIRST 2 ROWS ONLY , and SQL Server uses TOP .

Other filters: marks BETWEEN 70 AND 90 is inclusive at both ends (Vikram 78, Meera 85), and dept IN ('ECE', 'ME') matches any value in the list (Meera, Rohan, Priya).

A query is written SELECT first but processed in a fixed logical order: FROM, WHERE, GROUP BY, HAVING, SELECT, ORDER BY, LIMIT. That order explains why a column alias works in ORDER BY but not in WHERE, and why WHERE filters rows while HAVING filters groups:

A query is written SELECT first, but processed in the numbered order. Step 1, FROM: the DBMS starts from every row of students, all 5 of them.

- A query is written SELECT first, but processed in the numbered order. Step 1, FROM: the DBMS starts from every row of students, all 5 of them.
- Step 2, WHERE marks IS NOT NULL keeps a row only when the condition is TRUE. Rohan has no marks, so his row goes; 4 rows remain. SELECT has not run yet, so WHERE cannot use the alias best.
- Step 3, GROUP BY city collects the rows into 3 groups: Pune (1), Delhi (2), Chennai (1). From here on, each group is one row of the result.
- Step 4, HAVING filters groups, not rows, and can use aggregates. Delhi's best is 78, not above 80, so that group goes.
- Step 5, SELECT computes the output columns: one row per remaining group, city and MAX(marks) named best: Pune 91, Chennai 85.
- Step 6, ORDER BY best DESC sorts the result, and may use the alias because SELECT has run. Pune 91 then Chennai 85: without ORDER BY nothing guarantees any order.
- Step 7, LIMIT 1 keeps the first row of the sorted result: Pune, 91, the city with the best score among those above 80.

### NULL and three-valued logic

NULL means a value is missing or unknown. It is not zero and not an empty string, and any comparison with it gives a third truth value, UNKNOWN . WHERE keeps a row only when its condition is TRUE.

So Rohan's row slips through both of two complementary filters, and = NULL matches nothing at all:

Every comparison with Rohan's NULL is UNKNOWN, and NOT UNKNOWN is still UNKNOWN, so his row passes neither marks > 80 nor its opposite. marks = NULL is UNKNOWN for every row and returns nothing; only IS NULL finds him.

Arithmetic with NULL gives NULL ( marks + 5 is NULL for Rohan), and COALESCE(marks, 0) substitutes a value for NULL. MySQL's <=> is a null-safe equality that returns 1 for NULL <=> NULL ; standard SQL writes IS NOT DISTINCT FROM . NULL also explains the classic NOT IN trap with subqueries, covered in the joins note .

### Pattern matching with LIKE

LIKE compares a string with a pattern: % matches any run of characters (including none) and _ matches exactly one.

In MySQL's default collation ( utf8mb4_0900_ai_ci , case- and accent-insensitive) 'a%' also matches Asha; PostgreSQL's LIKE is case-sensitive and provides ILIKE . To match a literal % or _ , escape it: LIKE '50\%%' in MySQL, or LIKE '50!%%' ESCAPE '!' in any SQL. A pattern that starts with % cannot use an ordinary index, so it scans the whole table.

### DCL and TCL

DCL hands out and withdraws privileges:

```
GRANT
SELECT
,
INSERT
ON
college
.
students
TO
'intern'
@'localhost'
;
REVOKE
INSERT
ON
college
.
students
FROM
'intern'
@'localhost'
;
```

TCL groups statements so that they take effect together or not at all:

```
START
TRANSACTION
;
UPDATE
accounts
SET
balance
=
balance
-
1000
WHERE
id
=
1
;
UPDATE
accounts
SET
balance
=
balance
+
1000
WHERE
id
=
2
;
COMMIT
;
-- or ROLLBACK; to undo both
```

SAVEPOINT name marks a point inside a transaction that ROLLBACK TO SAVEPOINT name can return to. The transactions note explains what COMMIT and ROLLBACK guarantee.

### Common mistakes

- Writing = NULL instead of IS NULL : the comparison is UNKNOWN and matches nothing.
- Expecting WHERE x > 80 and WHERE x <= 80 to cover every row: NULLs are in neither.
- Relying on row order without ORDER BY : it can change between runs and versions.
- Running UPDATE or DELETE without WHERE by accident: test the WHERE with a SELECT first.
- Assuming TRUNCATE can be rolled back in MySQL: it commits implicitly.
- Assuming CHECK constraints were always enforced in MySQL: only from 8.0.16.

### Interview questions

What are the categories of SQL commands? DDL (CREATE, ALTER, DROP, TRUNCATE) for structure, DML (INSERT, UPDATE, DELETE) and DQL (SELECT) for data, DCL (GRANT, REVOKE) for permissions and TCL (COMMIT, ROLLBACK, SAVEPOINT) for transactions.

Why is TRUNCATE faster than DELETE? DELETE removes rows one at a time, logging each and firing triggers. TRUNCATE empties the table as a whole, much like dropping and recreating it, so it logs far less and skips per-row work. That is also why it cannot take a WHERE clause.

What is the difference between WHERE and HAVING? WHERE filters rows before grouping; HAVING filters groups after GROUP BY and can use aggregates such as COUNT(*). The aggregation note works both.

What is the difference between a primary key and a UNIQUE constraint? A table has one primary key, which never allows NULL. It may have many UNIQUE constraints, which in MySQL allow any number of NULLs.

What does NULL + 10 return? NULL. Any arithmetic with NULL gives NULL, and any comparison gives UNKNOWN; use COALESCE or IFNULL to substitute a value.

Which rows does WHERE marks NOT BETWEEN 70 AND 90 return in the table above? Asha (91) and Priya (67). Rohan is excluded because his marks are NULL, and NOT applied to UNKNOWN is still UNKNOWN.

What does a DEFAULT constraint do when you insert NULL explicitly? It does nothing; the default is used only when the column is omitted from the INSERT. Inserting NULL explicitly stores NULL, or fails if the column is NOT NULL.

Is DDL transactional? It depends on the DBMS. MySQL and Oracle commit implicitly around DDL statements, so they cannot be rolled back; PostgreSQL runs most DDL inside transactions and can roll it back.

Next, combine tables: SQL Joins . These queries are the ground of the SQL (Basic) skill test .

Practise on real tables: Scholarship Shortlist by CGPA or Hackathon Wins , Canteen Orders Not Placed With the FEST50 Coupon (the NULL trap) and the rest of the SQL practice problems .

### What is the difference between DELETE, TRUNCATE and DROP?

DELETE is DML and removes chosen rows (or all, without WHERE), firing triggers and keeping the table. TRUNCATE is DDL and empties the whole table quickly, resetting AUTO_INCREMENT. DROP removes the table itself, structure and all. In MySQL, TRUNCATE and DROP commit implicitly and cannot be rolled back.

### Why does WHERE column = NULL return no rows?

NULL means "unknown", so comparing anything with NULL gives UNKNOWN, not TRUE, and WHERE keeps only rows where the condition is TRUE. Use IS NULL or IS NOT NULL to test for NULL. MySQL also offers the null-safe operator <=>, which treats two NULLs as equal.

### What is the difference between CHAR and VARCHAR?

CHAR(n) is fixed length: shorter values are padded with spaces to n characters (MySQL strips the trailing spaces when reading). VARCHAR(n) stores only the characters given plus a small length prefix. Use CHAR for codes that are always the same length, such as a three-letter department code, and VARCHAR for names and text.

### What does the LIKE operator do in SQL?

LIKE matches a string against a pattern in which % stands for any sequence of characters, including none, and _ stands for exactly one character. name LIKE 'A%' finds names starting with A. In MySQL's default collations the match ignores case, while PostgreSQL's LIKE is case-sensitive and offers ILIKE instead.

### Is SELECT a DML or a DQL command?

Both labels are used. The SQL standard groups SELECT with the data manipulation statements, and many textbooks list it under DML. Others give it its own category, DQL (data query language), because it reads data without changing it. In an interview, mention both and say which convention you follow.


---

## Module 7: SQL Joins

*Original URL: https://codekairo.com/notes/dbms/sql-joins*

### Overview

Quick answer

### What is a join in SQL?

A join combines rows from two tables into one result by matching them on a condition, usually a foreign key equal to a primary key. An inner join keeps only matching pairs; left, right and full outer joins also keep unmatched rows from one or both sides, filling the missing columns with NULL. A cross join pairs every row with every row.

- The example tables
- Inner join
- Left outer join
- Right outer join
- Full outer join
- Cross join
- Self join
- Natural join and USING
- Duplicate rows: joining on non-key columns
- Where to put a filter in an outer join
- Join vs subquery
- Join types at a glance
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Relational design deliberately spreads facts over several tables: the employee's name in one, the department's name in another, linked by a key. A join puts them back together for a query. Interviewers test joins by giving two small tables and asking for the exact output, so this note runs every join type on the same two tables and shows every result row. Results are listed in a fixed order for reading; a real query needs ORDER BY to guarantee any order.

### The example tables

employees (Rohan has no department yet; manager_id refers to emp_id in the same table):

departments (HR has no employees):

Every join below starts from the same matching: each employee's dept_id against each department's.

The join reads employees one row at a time and looks in departments for every row whose dept_id equals this employee's. Each pair found becomes one result row.

- The join reads employees one row at a time and looks in departments for every row whose dept_id equals this employee's. Each pair found becomes one result row.
- Asha's dept_id is 10, which equals Engineering's: one result row, Asha with Engineering.
- Vikram's dept_id is 20, which equals Sales's: one result row, Vikram with Sales.
- Meera's dept_id is 10, which equals Engineering's: one result row, Meera with Engineering. A department may match any number of employees.
- Rohan's dept_id is NULL, and NULL = 10 is UNKNOWN, never TRUE, so no department matches. An inner join emits nothing; a left join still emits Rohan, with NULL for every department column.
- No employee pointed at HR, so a right join adds it with NULL for the employee. A full outer join keeps both padded rows: 3 matched pairs plus one unmatched row from each side.

### Inner join

An inner join returns one row for each pair of rows that satisfy the join condition. Rows without a partner disappear from both sides.

```
SELECT
e
.
name
,
d
.
dept_name
FROM
employees e
INNER
JOIN
departments d
ON
e
.
dept_id
=
d
.
dept_id
;
```

Rohan is missing because NULL = 10 is UNKNOWN, not TRUE, and HR is missing because no employee points to it. JOIN alone means INNER JOIN . A join whose condition is equality is an equi-join ; one with any other comparison ( < , BETWEEN ) is a theta join or non-equi join, used for example to match a salary to a pay band.

### Left outer join

A left join keeps every row of the left table. Where there is no match, the right table's columns are NULL.

```
SELECT
e
.
name
,
d
.
dept_name
FROM
employees e
LEFT
JOIN
departments d
ON
e
.
dept_id
=
d
.
dept_id
;
```

### Right outer join

A right join keeps every row of the right table. It is a left join with the tables swapped, and most teams write it as a left join for readability.

```
SELECT
e
.
name
,
d
.
dept_name
FROM
employees e
RIGHT
JOIN
departments d
ON
e
.
dept_id
=
d
.
dept_id
;
```

### Full outer join

A full outer join keeps every row from both sides: the matched pairs, the unmatched left rows and the unmatched right rows.

```
SELECT
e
.
name
,
d
.
dept_name
FROM
employees e
FULL
OUTER
JOIN
departments d
ON
e
.
dept_id
=
d
.
dept_id
;
-- PostgreSQL, SQL Server, Oracle
```

MySQL has no FULL OUTER JOIN. Emulate it with a left join plus the right join's unmatched rows:

```
SELECT
e
.
name
,
d
.
dept_name
FROM
employees e
LEFT
JOIN
departments d
ON
e
.
dept_id
=
d
.
dept_id
UNION
ALL
SELECT
e
.
name
,
d
.
dept_name
FROM
employees e
RIGHT
JOIN
departments d
ON
e
.
dept_id
=
d
.
dept_id
WHERE
e
.
emp_id
IS
NULL
;
```

The often-quoted version, LEFT JOIN … UNION … RIGHT JOIN , gives the same five rows here, but UNION removes duplicates, so it would also collapse genuinely repeated result rows (two employees with the same name in the same department). UNION ALL with the IS NULL filter does not.

### Cross join

A cross join is the Cartesian product: every row of one table paired with every row of the other, with no condition. Four employees and three departments give 4 × 3 = 12 rows.

```
SELECT
e
.
name
,
d
.
dept_name
FROM
employees e
CROSS
JOIN
departments d
;
```

A cross join pairs every employee with every department, with no condition: 4 × 3 = 12 result rows, one per cell.

- A cross join pairs every employee with every department, with no condition: 4 × 3 = 12 result rows, one per cell.
- An inner join keeps only the cells where ON e.dept_id = d.dept_id is TRUE: 3 of 12. Rohan's comparisons are NULL = 10, NULL = 20 and NULL = 30, all UNKNOWN, so his row has no TRUE cell.
- Outer joins add back what has no TRUE cell, padded with NULL: a left join adds Rohan's row, a right join HR's column, and a full outer join both.

Writing FROM employees, departments with no WHERE produces the same product, which is how accidental cross joins happen. Cross joins are useful for generating combinations, such as every size with every colour.

### Self join

A self join joins a table to itself through two aliases. To list each employee with their manager's name, treat one copy as employees ( e ) and the other as managers ( m ):

```
SELECT
e
.
name
AS
employee
,
m
.
name
AS
manager
FROM
employees e
LEFT
JOIN
employees m
ON
e
.
manager_id
=
m
.
emp_id
;
```

Read the table twice: as e, the employee, and as m, the manager. Each manager_id points at the row of m with that emp_id; Asha's NULL points nowhere, so an inner self join would drop her and a left one keeps her with a NULL manager.

Another self join finds pairs of colleagues in the same department: ON e.dept_id = m.dept_id AND e.emp_id < m.emp_id returns the single pair (Asha, Meera); the < stops each pair appearing twice and a person pairing with themselves.

### Natural join and USING

A natural join joins on every column the two tables share by name and shows each shared column once:

```
SELECT
*
FROM
employees
NATURAL
JOIN
departments
;
```

It is an inner join on dept_id , the only shared name. MySQL puts the shared column first. JOIN departments USING (dept_id) gives the same result while naming the column explicitly, whereas ON e.dept_id = d.dept_id with SELECT * shows dept_id twice. The danger of NATURAL JOIN is that it trusts names: if departments had a name column, the join would also require employees.name = departments.name and return nothing. Prefer ON or USING in real code.

### Duplicate rows: joining on non-key columns

A join returns one row per matching pair. When the join column is unique on one side (a key), each row on the other side matches at most once. When it is not unique on either side, rows multiply. Add a table of bonuses, where a department may have several:

For each value of the join column, the join returns (matching left rows) × (matching right rows):

Each line is one result row. Two Engineering employees meet two Engineering bonuses, so dept 10 alone gives 4 rows, and any SUM over employee columns now counts each of them twice.

This fan-out is the most common cause of wrong totals: join an order to its items and to its payments at once, and each item is repeated once per payment, so SUM(item_price) comes out too large. Aggregate each child table in a subquery first, then join the totals.

### Where to put a filter in an outer join

A condition in ON decides which rows match; a condition in WHERE filters the result afterwards. For an outer join the two differ:

### Join vs subquery

Some questions can be written either way, and the choice changes duplicates and NULL handling:

The last row is a classic trap. 30 NOT IN (10, 20, 10, NULL) expands to 30 <> 10 AND 30 <> 20 AND 30 <> 10 AND 30 <> NULL , and the last test is UNKNOWN, so HR is not returned. Use NOT EXISTS , or filter WHERE dept_id IS NOT NULL inside the subquery.

On performance, modern optimizers (MySQL 8 included) turn many IN and EXISTS subqueries into semi-joins, so the two forms often run the same plan. Use a join when you need columns from both tables, and EXISTS when you only need to test for a match.

### Common mistakes

- Forgetting that NULL never equals anything, so rows with NULL keys drop out of inner joins.
- Filtering the right table in WHERE after a left join, which silently turns it into an inner join.
- Summing after a join that fans out, which double-counts.
- Using NOT IN against a column that can hold NULL.
- Writing LEFT JOIN … UNION … RIGHT JOIN for a full join and losing genuine duplicates.
- Using NATURAL JOIN in production code that can later gain same-named columns.

### Interview questions

What is the difference between LEFT JOIN and RIGHT JOIN? A left join keeps all rows of the table before the keyword and a right join all rows of the table after it. A LEFT JOIN B returns the same rows as B RIGHT JOIN A ; only the column order differs.

If table A has 4 rows and B has 3, what is the minimum and maximum size of A INNER JOIN B? Of A LEFT JOIN B? An inner join returns between 0 and 12 rows. A left join returns at least 4 rows (every row of A appears) and at most 12.

How do you find employees who have no department? SELECT name FROM employees WHERE dept_id IS NULL if NULL means unassigned. To also catch department ids that do not exist in departments , left join and keep rows where d.dept_id IS NULL .

How do you write a full outer join in MySQL? A left join, then UNION ALL with a right join filtered to rows where the left table's key is NULL. Using plain UNION removes duplicate rows that may be genuine.

What is a self join? Give a use. A table joined to itself under two aliases. It finds each employee's manager, pairs of rows in the same group, or consecutive events in a log table.

Why can NOT IN return no rows when you expect some? If the subquery returns a NULL, every x NOT IN (…) test becomes UNKNOWN, and WHERE drops UNKNOWN rows. NOT EXISTS does not have this problem.

How does a database execute a join? With a nested-loop join (for each outer row, look up matches, ideally through an index), a hash join (build a hash table on the smaller input, probe it with the other) or a sort-merge join (sort both inputs on the key and merge). MySQL 8.0.18 and later can use hash joins; PostgreSQL implements all three.

Is a cross join ever useful? Yes: generating every combination (dates × stores for a report with zero-filled days, sizes × colours) or joining to a one-row table of parameters. Accidental cross joins come from a forgotten join condition.

Next, summarize rows with grouping and subqueries: SQL GROUP BY, HAVING and Subqueries . Joins are the heart of the SQL (Basic) skill test .

Practise joins on real tables: Employees Earning More Than Their Manager (a self join), Hostel Students Who Never Ordered From the Canteen (an anti join) and Mock Test Sittings for Every Learner and Track (a cross join with a left join).

### What is the difference between INNER JOIN and LEFT JOIN?

An inner join returns only the rows that have a match in both tables. A left join returns every row of the left table; where a row has no match, the right table's columns come back as NULL. So a left join never returns fewer rows than the left table has.

### Does MySQL support FULL OUTER JOIN?

No. MySQL has no FULL OUTER JOIN keyword. You emulate it with a LEFT JOIN, then UNION ALL with a RIGHT JOIN that keeps only the right rows with no match (WHERE the left key IS NULL). PostgreSQL, SQL Server and Oracle support FULL OUTER JOIN directly.

### What is a self join?

A self join joins a table to itself, using two aliases so each copy can be named. It answers questions about rows related to other rows of the same table, such as listing each employee with their manager when manager_id refers to emp_id in the same table.

### Why does a join return duplicate rows?

A join returns one row for every matching pair. If the join column is not unique on one side, a row on the other side matches several rows and appears once for each. Joining on a non-key column, or joining two child tables of the same parent, multiplies rows and inflates SUM and COUNT.

### What is the difference between a join and a subquery?

A join combines columns from both tables and can repeat a row once per match. A subquery with IN or EXISTS only filters the outer table, so each outer row appears at most once. Modern optimizers often rewrite one into the other, so choose the form that states the question most clearly.

### What is the difference between NATURAL JOIN and INNER JOIN?

A natural join matches on every column the two tables share by name, without an ON clause, and shows each shared column once. An inner join matches on the condition you write. Natural joins are risky: adding a same-named column such as updated_at later silently changes the join.


---

## Module 8: SQL GROUP BY, HAVING and Subqueries

*Original URL: https://codekairo.com/notes/dbms/sql-aggregation-and-subqueries*

### Overview

Quick answer

### What do GROUP BY and HAVING do in SQL?

GROUP BY collapses rows that share the same values in the listed columns into one group, so aggregate functions such as COUNT, SUM and AVG return one value per group. HAVING then filters those groups by a condition on the aggregates, for example keeping departments whose average salary exceeds 60,000. WHERE filters individual rows before grouping; HAVING filters groups after it.

- The example tables
- Aggregate functions and NULLs
- GROUP BY
- HAVING vs WHERE
- Subqueries
- Window functions
- Second and Nth highest salary, three ways
- Logical order of SQL clauses
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Most questions asked of a database are summaries: how many students per branch, the average package per company, the top scorer in each section. SQL answers them with aggregate functions , GROUP BY and HAVING , and answers "compared with what?" with subqueries and window functions . This note works all of them on one small table, shows exact results (checked on MySQL 8), solves the "second highest salary" question three ways, and ends with the logical order in which SQL evaluates a query, which explains most of the errors you will meet.

### The example tables

employees (Neha's salary is not yet set):

departments : Engineering in Bengaluru, Sales in Mumbai, HR in Mumbai, and Legal in Delhi (Legal has no employees).

### Aggregate functions and NULLs

An aggregate function turns many rows into one value. Every aggregate except COUNT(*) ignores NULLs :

Whether NULL should count as zero is a business decision, and AVG silently decides it for you. Two edge cases: over zero rows COUNT returns 0 but SUM , AVG , MIN and MAX return NULL. MySQL prints the average of integers with four decimal places.

### GROUP BY

GROUP BY splits the rows into groups with equal values in the listed columns, and each aggregate is computed per group:

```
SELECT
dept
,
COUNT
(
*
)
AS
staff
,
COUNT
(
salary
)
AS
paid
,
SUM
(
salary
)
AS
total
,
AVG
(
salary
)
AS
avg_salary
FROM
employees
GROUP
BY
dept
ORDER
BY
dept
;
```

The 7 rows as the table stores them, departments mixed. GROUP BY dept will gather the rows that share a dept value into one group each.

- The 7 rows as the table stores them, departments mixed. GROUP BY dept will gather the rows that share a dept value into one group each.
- Rows with equal dept values form one group: Engineering (3), HR (2), Sales (2). Nothing is computed yet; each aggregate will run once inside each group.
- Each group collapses to one row. COUNT(*) counts rows, but COUNT(salary), SUM and AVG skip NULL: HR has 2 staff, 1 paid, and its average is 50000 / 1, not / 2.

The rule: every column in the SELECT list must either appear in GROUP BY or be inside an aggregate. SELECT dept, name, MAX(salary) … GROUP BY dept is ambiguous (which name?), and MySQL 8, whose default sql_mode includes ONLY_FULL_GROUP_BY , rejects it with error 1055. Older MySQL versions returned an arbitrary name, which is why old answers online sometimes "work". All NULLs in a grouping column form one group.

### HAVING vs WHERE

HAVING filters groups, so it can test aggregates:

```
SELECT
dept
,
AVG
(
salary
)
AS
avg_salary
FROM
employees
GROUP
BY
dept
HAVING
AVG
(
salary
)
>
60000
;
```

Result: Engineering 85000.0000 and Sales 62500.0000; HR (50000) is dropped. Combining both filters shows the order in which they run:

```
SELECT
dept
,
COUNT
(
*
)
AS
high_earners
FROM
employees
WHERE
salary
>
60000
GROUP
BY
dept
HAVING
COUNT
(
*
)
>=
2
;
```

WHERE runs first, on single rows: 4 rows have a salary over 60000. Rohan's 60000 is not greater, and Neha's NULL gives UNKNOWN, which WHERE drops like FALSE.

- WHERE runs first, on single rows: 4 rows have a salary over 60000. Rohan's 60000 is not greater, and Neha's NULL gives UNKNOWN, which WHERE drops like FALSE.
- GROUP BY sees only the 4 survivors: Engineering with 3 and Sales with 1. HR has no group at all, because WHERE removed both of its rows before grouping began.
- HAVING runs last, on whole groups, so it may test COUNT(*). Engineering's 3 passes and Sales's 1 fails the test >= 2: the result is one row, Engineering, 3.

The result is one row, Engineering, 3 .

### Subqueries

A subquery is a query inside another query. It can return one value, a list, or a table.

Scalar subquery (one value): employees paid more than the company average of 71666.67.

```
SELECT
name
,
salary
FROM
employees
WHERE
salary
>
(
SELECT
AVG
(
salary
)
FROM
employees
)
;
```

Result: Asha 90000, Vikram 75000, Meera 90000.

IN subquery (a list): employees in Mumbai departments. WHERE dept IN (SELECT dept FROM departments WHERE city = 'Mumbai') returns Rohan, Priya, Kabir and Neha.

EXISTS (is there at least one row?): departments with someone earning over 80000.

```
SELECT
d
.
dept
FROM
departments d
WHERE
EXISTS
(
SELECT
1
FROM
employees e
WHERE
e
.
dept
=
d
.
dept
AND
e
.
salary
>
80000
)
;
```

Result: Engineering. With NOT EXISTS (SELECT 1 FROM employees e WHERE e.dept = d.dept) the result is Legal, the department with no employees. EXISTS only checks whether a row exists, so SELECT 1 is the convention. Prefer NOT EXISTS to NOT IN whenever the subquery's column can be NULL; the joins note shows NOT IN returning nothing because of one NULL.

Correlated subquery (refers to the outer row): employees who earn more than their own department's average.

```
SELECT
e
.
name
,
e
.
dept
,
e
.
salary
FROM
employees e
WHERE
e
.
salary
>
(
SELECT
AVG
(
x
.
salary
)
FROM
employees x
WHERE
x
.
dept
=
e
.
dept
)
;
```

The subquery refers to e.dept, the outer row's department, so it is evaluated again for each outer row. For Asha, it averages Engineering: 85000. 90000 > 85000 is TRUE, so Asha is kept.

- The subquery refers to e.dept, the outer row's department, so it is evaluated again for each outer row. For Asha, it averages Engineering: 85000. 90000 > 85000 is TRUE, so Asha is kept.
- Vikram: Engineering's average is 85000, computed again for this row. 75000 > 85000 is FALSE, so Vikram is dropped.
- Meera: Engineering's average is 85000, computed again for this row. 90000 > 85000 is TRUE, so Meera is kept.
- Rohan: Sales's average is 62500. 60000 > 62500 is FALSE, so Rohan is dropped.
- Priya: Sales's average is 62500, computed again for this row. 65000 > 62500 is TRUE, so Priya is kept.
- Kabir earns 50000 and HR's average is 50000 (the NULL salary is skipped): equal is not greater, so the row is dropped.
- Neha's salary is NULL, so NULL > 50000 is UNKNOWN and the row is dropped, even though the subquery itself ran and returned 50000.
- 3 rows survive: Asha, Meera, Priya. Logically the subquery ran 7 times for only 3 different answers, which is why optimizers often rewrite it as a join with each department's average computed once.

Changing > to = and AVG to MAX gives the top earners per department: Asha and Meera (tied), Priya and Kabir.

### Window functions

A window function computes a value for each row from a set of related rows (its window) without collapsing them the way GROUP BY does. OVER (PARTITION BY … ORDER BY …) defines the window. MySQL supports them from version 8.0.

The three ranking functions differ only on ties:

```
SELECT
name
,
salary
,
ROW_NUMBER
(
)
OVER
(
ORDER
BY
salary
DESC
,
emp_id
)
AS
row_num
,
RANK
(
)
OVER
(
ORDER
BY
salary
DESC
)
AS
rnk
,
DENSE_RANK
(
)
OVER
(
ORDER
BY
salary
DESC
)
AS
dense_rnk
FROM
employees
WHERE
salary
IS
NOT
NULL
;
```

ROW_NUMBER never ties ( emp_id breaks the tie so the numbering is repeatable), RANK leaves a gap after a tie (1, 1, 3), and DENSE_RANK does not (1, 1, 2). Had Neha's row been included, MySQL would place the NULL last in descending order with rank 7 and dense rank 6.

PARTITION BY restarts the window for each group. RANK() OVER (PARTITION BY dept ORDER BY salary DESC) ranks Asha and Meera 1 and Vikram 3 in Engineering, Priya 1 and Rohan 2 in Sales, and Kabir 1 in HR. To keep exactly one top earner per department, number the rows and filter in an outer query, because window functions cannot appear in WHERE :

```
SELECT
dept
,
name
,
salary
FROM
(
SELECT
dept
,
name
,
salary
,
ROW_NUMBER
(
)
OVER
(
PARTITION
BY
dept
ORDER
BY
salary
DESC
,
emp_id
)
AS
rn
FROM
employees
)
t
WHERE
rn
=
1
;
```

Result: Engineering Asha 90000, HR Kabir 50000, Sales Priya 65000. Ordinary aggregates also work as windows: AVG(salary) OVER (PARTITION BY dept) puts each department's average beside every row (85000 on each Engineering row).

### Second and Nth highest salary, three ways

The salaries in descending order are 90000, 90000, 75000, 65000, 60000, 50000 and NULL, so the second highest distinct salary is 75000 .

```
-- 1. MAX below the MAX
SELECT
MAX
(
salary
)
AS
second_highest
FROM
employees
WHERE
salary
<
(
SELECT
MAX
(
salary
)
FROM
employees
)
;
-- 2. Sort distinct salaries and skip one
SELECT
DISTINCT
salary
FROM
employees
ORDER
BY
salary
DESC
LIMIT
1
OFFSET
1
;
-- 3. DENSE_RANK
SELECT
DISTINCT
salary
FROM
(
SELECT
salary
,
DENSE_RANK
(
)
OVER
(
ORDER
BY
salary
DESC
)
AS
rnk
FROM
employees
WHERE
salary
IS
NOT
NULL
)
t
WHERE
rnk
=
2
;
```

ORDER BY salary DESC LIMIT 1 OFFSET 1 skips one row and returns the next. Without DISTINCT the tie at the top fills two rows, so the "second highest" comes back as 90000, the highest again.

- ORDER BY salary DESC LIMIT 1 OFFSET 1 skips one row and returns the next. Without DISTINCT the tie at the top fills two rows, so the "second highest" comes back as 90000, the highest again.
- SELECT DISTINCT salary keeps one copy of each value before the sort, so OFFSET 1 lands on 75000, the second highest distinct salary. The NULL is kept too, and sorts last.
- With the NULL filtered out, DENSE_RANK numbers the distinct values 1, 2, 3 with no gaps, so rank 2 is 75000. RANK skips a number after the tie, 1, 1, 3, so no row has rank 2 and the query would return nothing.

All three return 75000. How they generalize to the Nth highest:

A fourth classic uses a correlated count: keep the salary that exactly N−1 distinct salaries exceed, WHERE N - 1 = (SELECT COUNT(DISTINCT x.salary) FROM employees x WHERE x.salary > e.salary) . MySQL does not accept an expression such as N - 1 directly after OFFSET , so for a variable N use a prepared statement or the DENSE_RANK form.

### Logical order of SQL clauses

You write SELECT … FROM … WHERE … GROUP BY … HAVING … ORDER BY … LIMIT , but the DBMS evaluates the clauses in a different logical order:

SELECT is written first but runs fifth, after the rows are filtered and grouped. So WHERE cannot see aliases or aggregates, which do not exist yet, while ORDER BY, running later, can use both.

Window functions are computed in the SELECT step, so they see only the rows that survived WHERE and HAVING , and they cannot be used in WHERE either. The optimizer may physically reorder work, but never in a way that changes this result.

### Common mistakes

- Expecting AVG to count NULLs as zero: it ignores them.
- Selecting a column that is neither grouped nor aggregated: an error under ONLY_FULL_GROUP_BY , a random value in old MySQL.
- Filtering an aggregate in WHERE instead of HAVING .
- Using a window function in WHERE : compute it in a derived table and filter outside.
- Forgetting DISTINCT in the LIMIT … OFFSET answer to the second highest salary.
- Using RANK where DENSE_RANK is meant for "Nth highest".

### Interview questions

**What does SELECT COUNT(*) FROM employees GROUP BY dept return for an empty table?** No rows. With no rows there are no groups, whereas SELECT COUNT(*) FROM employees without GROUP BY returns one row holding 0.

Can you use HAVING without GROUP BY? Yes. The whole result is then one group, so SELECT COUNT(*) FROM employees HAVING COUNT(*) > 5 returns one row (7) or none.

What is the difference between a correlated and a non-correlated subquery? A non-correlated subquery does not refer to the outer query and is evaluated once. A correlated one refers to the outer row and is logically evaluated per outer row, though optimizers often turn it into a join.

IN or EXISTS: which should you use? They give the same result for positive tests, and optimizers often run both as a semi-join. For negative tests use NOT EXISTS, because NOT IN returns nothing if the subquery yields a NULL.

How do you find the highest-paid employee in each department? Either a correlated subquery comparing salary with the department's MAX, which returns all tied employees, or ROW_NUMBER (or RANK) partitioned by department and filtered to 1 in an outer query.

Write a query for departments with more than one employee. SELECT dept, COUNT(*) FROM employees GROUP BY dept HAVING COUNT(*) > 1 . Here it returns Engineering 3, HR 2 and Sales 2.

What is the difference between GROUP BY and a window function's PARTITION BY? GROUP BY returns one row per group. PARTITION BY keeps every row and attaches the per-group value to each, so you can show a salary beside its department average.

In what order is a SELECT statement evaluated? FROM and joins, WHERE, GROUP BY, HAVING, SELECT (including window functions), DISTINCT, ORDER BY, LIMIT. Most "unknown column" and "invalid use of group function" errors follow from this order.

Next, make several statements succeed or fail together: Transactions and ACID Properties in DBMS . Window functions and subqueries are examined in the SQL (Intermediate) skill test .

Practise on real tables: Second-Best Innings in the College Cup (the "second highest" problem), Quiz Team Standings With Shared Places (DENSE_RANK) and Students Who Attended Every Fest Workshop (HAVING with a subquery).

### What is the difference between WHERE and HAVING?

WHERE filters rows before they are grouped and cannot use aggregate functions. HAVING filters groups after GROUP BY and can use aggregates such as COUNT(*) or AVG(salary). Put row conditions in WHERE so fewer rows reach the grouping step, and only aggregate conditions in HAVING.

### What is the difference between COUNT(*) and COUNT(column)?

COUNT(*) counts rows, whatever they contain. COUNT(column) counts rows where that column is not NULL, and COUNT(DISTINCT column) counts distinct non-NULL values. On a table of seven employees where one salary is NULL, they return 7, 6 and the number of different salaries.

### How do you find the second highest salary in SQL?

Three standard ways: SELECT MAX(salary) WHERE salary is below the overall MAX; SELECT DISTINCT salary ORDER BY salary DESC LIMIT 1 OFFSET 1; or DENSE_RANK() over salary descending, keeping rank 2. The DISTINCT matters: without it, a tie for the top salary makes the second row another copy of the highest.

### What is the difference between RANK and DENSE_RANK?

Both give tied rows the same rank. RANK then skips numbers, so two rows tied at first are followed by rank 3. DENSE_RANK does not skip, so the next row gets rank 2. ROW_NUMBER never ties: it numbers rows 1, 2, 3 in the window's order.

### What is a correlated subquery?

A correlated subquery refers to a column of the outer query, so it is logically re-evaluated for each outer row. Finding employees who earn more than their own department's average needs one, because the average depends on each row's department. Uncorrelated subqueries run once.

### Why can't I use a column alias in WHERE?

WHERE is evaluated before SELECT, so the alias does not exist yet when rows are filtered. Repeat the expression, or compute it in a derived table or CTE and filter outside. Standard SQL allows SELECT aliases in ORDER BY; MySQL also accepts them in GROUP BY and HAVING.


---

## Module 9: Transactions and ACID Properties in DBMS

*Original URL: https://codekairo.com/notes/dbms/transactions-and-acid*

### Overview

Quick answer

### What are the ACID properties of a transaction?

ACID names four guarantees a DBMS gives a transaction. Atomicity: all of its changes happen or none do. Consistency: it takes the database from one valid state to another. Isolation: concurrent transactions do not see each other's partial work. Durability: once committed, its changes survive crashes. Logs and recovery provide atomicity and durability; concurrency control provides isolation.

- What a transaction is
- Transaction states
- Atomicity
- Consistency
- Isolation
- Durability
- COMMIT, ROLLBACK and SAVEPOINT
- Write-ahead logging and recovery
- Shadow paging
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A database is used by many people at once, and machines crash. A transaction is the tool that keeps data correct through both: a group of operations that the DBMS treats as one indivisible unit. Moving ₹1,000 from one account to another is two updates, and a world in which only one of them happened is a world where money vanished or appeared. This note defines transactions and their states, works each ACID property on that transfer, and explains how a DBMS actually delivers each one: logs, recovery, locking, and write-ahead logging.

### What a transaction is

A transaction is a sequence of operations on the database that forms one logical unit of work. In theory courses it is written with two operations: read(X) copies item X from the database into a local variable, and write(X) copies the local variable back. The transfer T1 of ₹1,000 from account A (₹5,000) to account B (₹3,000) takes seven steps:

T1 moves ₹1,000 from A (₹5,000) to B (₹3,000). read copies an item from the database into T1's own variable, and write copies the variable back.

- T1 moves ₹1,000 from A (₹5,000) to B (₹3,000). read copies an item from the database into T1's own variable, and write copies the variable back.
- read(A) copies A = 5000 into T1's variable. Nothing in the database changes.
- A := A − 1000 changes only T1's own copy, now A = 4000. The database still holds A = 5000.
- write(A) puts 4000 into the database while B still holds 3000: the database now shows a total of 7000, ₹1,000 short, until write(B) runs.
- read(B) copies B = 3000 into T1's variable. Nothing in the database changes.
- B := B + 1000 changes only T1's own copy, now B = 4000. The database still holds B = 3000.
- write(B) stores 4000. The database is consistent again, A + B = 8000, but T1 has not committed yet, so a crash now would still roll it back.
- Commit: both writes are in, A = 4000 and B = 4000, and the total is 8000 again. Every ACID property exists so that nobody acts on the state between write(A) and write(B).

Every ACID property is about making sure nobody, including a crash, ever acts on the ₹7,000 state between write(A) and write(B).

### Transaction states

A transaction runs in the active state. When its last statement has run it is partially committed, its changes possibly still only in memory, and it is committed once its commit record reaches stable storage.

- A transaction runs in the active state. When its last statement has run it is partially committed, its changes possibly still only in memory, and it is committed once its commit record reaches stable storage.
- Any error, deadlock or crash sends an active transaction to failed, and so can a failed log write after the last statement. Rolling back its changes makes it aborted; the system then restarts it or kills it.

After an abort the system either restarts the transaction (if the failure was not its own fault, such as a deadlock) or kills it (if its logic was wrong). Some textbooks add a final Terminated state reached after commit or abort.

### Atomicity

All or nothing. Either every operation of the transaction is reflected in the database, or none is.

Suppose the server crashes just after write(A). Without atomicity the database would restart with A = 4000 and B = 3000, and ₹1,000 would be gone. With it, the recovery manager finds that T1 never committed and undoes its write, restoring A to 5000.

How: before changing a value, the DBMS logs the old value. Rollback and crash recovery replay these undo records backwards. MySQL's InnoDB keeps them in undo logs (which also serve its multi-version reads).

### Consistency

Valid state to valid state. If the database satisfies its rules before the transaction, it satisfies them afterwards. For the transfer, the rule is that A + B is the same before and after (₹8,000), and that no balance goes negative.

How: the DBMS enforces declared constraints (primary and foreign keys, NOT NULL, CHECK) and rejects a statement that would break one. Rules it was never told, such as "transfers conserve money", are kept by the transaction's own logic. Consistency is therefore the one property shared with the application; atomicity and isolation make sure that correct logic stays correct despite crashes and concurrency.

### Isolation

Concurrent transactions do not see each other's partial work. The result of running transactions concurrently must equal the result of running them one after another in some order.

Suppose T2 computes the bank's total, A + B, while T1 is half done. The DBMS keeps that total right with concurrency control : locking, or multi-version concurrency control (MVCC), which InnoDB and PostgreSQL use:

With no isolation, T2 reads A after T1's write(A) but B before write(B): 7000, a total that never existed in any committed state. This is what isolation forbids.

- With no isolation, T2 reads A after T1's write(A) but B before write(B): 7000, a total that never existed in any committed state. This is what isolation forbids.
- With multi-version concurrency control, T2 reads the committed versions as of its own start, A = 5000 and B = 3000, even though T1 has already written a newer A. The total is 8000, and nobody waited.
- With locking, T1 holds an exclusive lock on A from write(A) until it commits, so T2's read(A) waits and T2 runs after the commit. It sees 8000, the state after the transfer, at the cost of waiting.

Full isolation (serializability) costs throughput, so SQL offers weaker isolation levels that allow some anomalies. The concurrency control note covers schedules, locks and isolation levels.

### Durability

Committed means permanent. Once the user is told the transfer succeeded, it survives a power cut, a crash or a restart.

Suppose the server crashes a moment after T1 commits, before the changed pages have been written from memory to disk. On restart, the recovery manager finds T1's commit record in the log and redoes its writes, so A = 4000 and B = 4000.

How: the commit is acknowledged only after the transaction's log records are forced to stable storage. In InnoDB this is the redo log, flushed at every commit by default ( innodb_flush_log_at_trx_commit = 1 ); the settings 0 and 2 trade up to about a second of committed transactions on a crash for speed. Durability on one machine does not protect against losing the disk itself; that needs replicas and backups.

### COMMIT, ROLLBACK and SAVEPOINT

```
START
TRANSACTION
;
UPDATE
accounts
SET
balance
=
balance
-
1000
WHERE
id
=
'A'
;
SAVEPOINT
after_debit
;
UPDATE
accounts
SET
balance
=
balance
+
1000
WHERE
id
=
'B'
;
ROLLBACK
TO
SAVEPOINT
after_debit
;
-- undoes only the credit to B
COMMIT
;
-- A = 4000, B = 3000
```

COMMIT makes the changes permanent. ROLLBACK undoes everything since START TRANSACTION . SAVEPOINT name marks a point inside the transaction, and ROLLBACK TO SAVEPOINT name undoes only the work after it while the transaction stays open. The example deliberately commits half a transfer to show that a savepoint gives you partial rollback, and that keeping the result consistent is your job.

Three MySQL behaviours worth knowing:

- Autocommit is on by default, so each statement outside START TRANSACTION is a transaction of its own.
- A failing statement does not abort the transaction. If the second UPDATE breaks a CHECK constraint, InnoDB undoes that statement only; the first stays in place until you ROLLBACK or COMMIT . Applications must roll back on error themselves. A deadlock, by contrast, rolls back the whole transaction.
- DDL commits implicitly , so a CREATE TABLE or TRUNCATE inside a transaction commits what came before it.

### Write-ahead logging and recovery

The log is a sequential file of records describing every change. T1 writes four: <T1 start> , then <T1, A, 5000, 4000> and <T1, B, 3000, 4000> (transaction, item, old value, new value), then <T1 commit> .

Write-ahead logging (WAL) has two rules:

- Before a changed data page is written to disk, the log records for its changes must be on stable storage. This keeps undo possible.
- A transaction is committed only when all its log records, up to and including the commit record, are on stable storage. This keeps redo possible.

Writing the log is cheap because it is sequential, so the DBMS can keep data pages in memory and write them back lazily. Real systems allow uncommitted changes to reach disk (called steal ) and do not force pages to disk at commit ( no-force ), so recovery needs both undo and redo:

T1's log: a start record, one record per write holding the item's old and new value, and a commit record. Write-ahead logging puts each record on stable storage before the data page it describes.

- T1's log: a start record, one record per write holding the item's old and new value, and a commit record. Write-ahead logging puts each record on stable storage before the data page it describes.
- Crash after the A record. The page holding A = 4000 had already reached disk, but there is no commit record, so recovery must undo T1, putting the old value 5000 back from the log.
- Crash after the B record: both new values may be on disk, and still no commit record. Recovery undoes in reverse log order, B first and then A, restoring A = 5000 and B = 3000.
- Crash after the commit record, before either data page was written. T1 committed, so recovery must redo it from the log's new values: A = 4000, B = 4000. That is durability.

Recovery redoes committed transactions and undoes uncommitted ones. To avoid scanning the whole log, the DBMS writes periodic checkpoints recording which transactions were active and which pages were dirty, and recovery starts from the last one. ARIES, published at IBM in 1992, is the standard recovery algorithm built on these ideas, with analysis, redo and undo passes. Older textbooks also describe deferred update (nothing reaches the database before commit, so recovery needs only redo) and immediate update (changes may reach it early, so recovery needs undo and redo).

### Shadow paging

Shadow paging achieves atomicity and durability without a log of changes. The database is a set of pages found through a page table. When a transaction starts, the current page table is copied; the original becomes the shadow page table and is never modified. Each page the transaction writes is copied to a new location, and only the new table points to it.

While T runs, each page it writes is copied to a new place (P2', P4') and only the current table points at the copies. The db root still names the shadow table, which is never modified.

- While T runs, each page it writes is copied to a new place (P2', P4') and only the current table points at the copies. The db root still names the shadow table, which is never modified.
- Commit: flush the new pages and the current table, then switch the db root to the current table in one atomic write. The old P2 and P4 are now garbage to collect.
- A crash or abort before the switch: the db root still names the shadow table, which describes the old, consistent database. The copies are simply discarded; nothing needs undoing or redoing.

It makes recovery trivial, but it scatters related pages across the disk, leaves old pages to garbage-collect, makes every commit write a page table, and is hard to combine with concurrent transactions. That is why mainstream relational systems use WAL; the copy-on-write idea survives in some storage engines and file systems.

### Common mistakes

- Saying the DBMS alone guarantees consistency: it enforces declared constraints; business invariants are the transaction's job.
- Assuming an error inside a MySQL transaction rolls it back: only the failing statement is undone.
- Equating "committed" with "written to the data files": it means the log is on stable storage.
- Thinking isolation means transactions run one at a time: they run concurrently, with results equivalent to some serial order.
- Treating durability as backup: it covers crashes, not a destroyed disk.

### Interview questions

Explain ACID with an example. Use a transfer of ₹1,000 from A to B. Atomicity: both updates or neither. Consistency: the total is conserved and no balance goes negative. Isolation: a concurrent report never sees money in flight. Durability: once confirmed, the transfer survives a crash.

Which component of a DBMS provides each property? The recovery manager, through the log, provides atomicity and durability. The concurrency control manager provides isolation. Integrity constraints and the application's transaction logic provide consistency.

What are the states of a transaction? Active, partially committed, committed, failed and aborted, with terminated in some books. A transaction can fail from the active or partially committed state, and an aborted one is either restarted or killed.

What is a savepoint? A named point inside a transaction. ROLLBACK TO SAVEPOINT undoes the work done after it without ending the transaction, which is useful for retrying one step of a long transaction.

Why does a DBMS need both undo and redo during recovery? Because the buffer manager may write uncommitted changes to disk (so they must be undone) and need not write committed changes before acknowledging the commit (so they must be redone). Undo restores atomicity; redo restores durability.

What is a checkpoint? A point at which the DBMS records the active transactions and flushes or notes the dirty pages, so recovery can start from it rather than from the beginning of the log. It bounds restart time.

What is the difference between WAL and shadow paging? WAL updates pages in place and logs every change so it can undo and redo. Shadow paging never overwrites a page, writing copies and switching a page-table pointer at commit; it needs no undo or redo but fragments data and handles concurrency poorly.

Does autocommit mean every statement is durable? Yes, with the default log-flush setting: under autocommit each statement commits on its own, so its changes are durable once it returns. It also means a multi-statement change has no atomicity unless you wrap it in START TRANSACTION and COMMIT.

Next, what happens when many transactions run at once: Concurrency Control in DBMS . Transactions and isolation appear in the SQL (Intermediate) skill test .

### What is a transaction in DBMS?

A transaction is a sequence of reads and writes that the DBMS treats as one logical unit of work, such as moving money between two accounts. It either commits, making all its changes permanent, or aborts, leaving no trace. Transactions are how a database stays correct under crashes and concurrent users.

### How does a DBMS ensure atomicity?

It records every change in a log before applying it, keeping the old value (undo information). If the transaction aborts, or the system crashes before it commits, the recovery manager uses the log to undo its changes. MySQL's InnoDB keeps this information in undo logs.

### How does a DBMS ensure durability?

A transaction counts as committed only after its log records, including the commit record, are forced to stable storage such as disk. After a crash, the recovery manager replays (redoes) committed changes from the log even if the data pages never reached disk. This is write-ahead logging.

### What is the difference between COMMIT and ROLLBACK?

COMMIT ends a transaction and makes all its changes permanent and visible to others. ROLLBACK ends it and undoes all its changes since it began, or since a named savepoint with ROLLBACK TO SAVEPOINT. After either, a new transaction starts with the next statement.

### Which ACID property is the application's responsibility?

Consistency, largely. The DBMS enforces declared constraints such as keys, foreign keys and CHECK, but it cannot know business rules it was never told, such as "a transfer must not create money". The transaction's own logic must preserve them; atomicity and isolation then keep that logic safe under failures and concurrency.

### What is write-ahead logging?

Write-ahead logging (WAL) is the rule that a change's log record must reach stable storage before the changed data page does, and that a transaction commits only once all its log records are stable. It lets the DBMS write data pages lazily while still being able to undo and redo any change after a crash.


---

## Module 10: Concurrency Control in DBMS

*Original URL: https://codekairo.com/notes/dbms/concurrency-control*

### Overview

Quick answer

### What is concurrency control in DBMS?

Concurrency control is the part of a DBMS that lets many transactions run at the same time while keeping the result equal to running them one after another in some order (serializability). It prevents anomalies such as dirty reads and lost updates using locks (two-phase locking), timestamps or multiple versions of data, and it detects or prevents the deadlocks that locking can cause.

- Schedules
- Conflict serializability
- Worked example: a precedence graph
- View serializability
- Recoverable and cascadeless schedules
- Concurrency anomalies
- Isolation levels
- Locks: shared and exclusive
- Two-phase locking
- Timestamp ordering
- Deadlock handling
- Common mistakes
- Interview questions
- Common questions
- Test yourself

A database serves hundreds of transactions at once. Running them strictly one after another would be correct but slow, because each spends most of its time waiting for disk, network or the user. Running them interleaved is fast, but some interleavings produce results no serial run could: lost money, wrong totals, phantom rows. Concurrency control decides which interleavings to allow. This note defines when a schedule is correct, works a precedence graph, lists the anomalies and the isolation levels that permit them, and covers the protocols that enforce correctness: two-phase locking, timestamp ordering and deadlock handling.

### Schedules

A schedule is the order in which the operations of several transactions are executed, keeping each transaction's own order. Ri(X) and Wi(X) mean transaction Ti reads or writes item X.

- A serial schedule runs transactions one at a time: all of T1, then all of T2. Always correct, never concurrent.
- A concurrent (non-serial) schedule interleaves them.
- A schedule is serializable if it is equivalent to some serial schedule of the same transactions. Serializability is the definition of correctness for concurrent execution.

### Conflict serializability

Two operations conflict if they belong to different transactions, access the same item, and at least one is a write:

A schedule is conflict serializable if swapping adjacent non-conflicting operations can turn it into a serial schedule. The test is the precedence graph : one node per transaction, and an edge Ti → Tj whenever an operation of Ti conflicts with a later operation of Tj. The schedule is conflict serializable if and only if the graph has no cycle , and any topological order of the graph is an equivalent serial order.

### Worked example: a precedence graph

Schedule S1, with commits omitted:

Check every pair of operations on the same item from different transactions, in schedule order:

Scan the schedule for conflicts: two operations of different transactions on the same item, at least one a write. Each conflict adds an edge from the earlier operation's transaction to the later one's.

- Scan the schedule for conflicts: two operations of different transactions on the same item, at least one a write. Each conflict adds an edge from the earlier operation's transaction to the later one's.
- W1(A) at step 3 and R3(A) at step 4: same item A, a write then a read. Edge T1 → T3.
- W2(B) at step 5 and R1(B) at step 6: same item B, a write then a read. Edge T2 → T1.
- R2(B) at step 2 and W3(B) at step 7: same item B, a read then a write. Edge T2 → T3.
- W2(B) at step 5 and W3(B) at step 7: same item B, both write. The edge T2 → T3 is already there; a second conflict adds nothing.
- R1(B) at step 6 and W3(B) at step 7: same item B, a read then a write. The edge T1 → T3 is already there; a second conflict adds nothing.
- The graph has 3 edges and no cycle, so S1 is conflict serializable. T2 has no incoming edge and goes first, then T1, then T3: the only topological order, and the equivalent serial schedule.

Five pairs conflict, giving the edges T2 → T1, T1 → T3 and T2 → T3. R1(A) with R3(A) and R2(B) with R1(B) are pairs of reads, so they add nothing. There is no cycle, so S1 is conflict serializable, equivalent to the serial order T2, T1, T3 .

Now the schedule S2: R1(A), R2(A), W1(A), W2(A), where T1 debits ₹1,000 and T2 credits ₹500:

R1(A) comes before W2(A), giving T1 → T2, and R2(A) comes before W1(A), giving T2 → T1: a cycle, so S2 is not conflict serializable. Both read 5000, and T2's write of 5500 wipes out T1's debit.

S2 is not conflict serializable. It is the lost update: both read the same balance, and T2's write wipes out T1's.

### View serializability

Two schedules are view equivalent if every transaction reads the same values in both (same initial reads, same reads-from) and the same transaction makes the final write of each item. A schedule is view serializable if it is view equivalent to a serial one.

Every conflict-serializable schedule is view serializable, but not the reverse. S3: R1(A), W2(A), W1(A), W3(A) has edges T1 → T2 and T2 → T1, a cycle, so it is not conflict serializable. Yet it is view equivalent to T1, T2, T3: T1 reads the initial A in both, and T3 writes the final A in both. The difference comes from blind writes (W2 and W3 write A without reading it). Testing view serializability is NP-complete, which is why systems enforce conflict serializability.

### Recoverable and cascadeless schedules

Serializability ignores aborts. Three stronger properties handle them:

Example of a non-recoverable schedule: W1(A), R2(A), commit T2, then T1 aborts. T2 has committed using a value that never officially existed, and durability forbids undoing it. Each class contains the next: every strict schedule is cascadeless, and every cascadeless schedule is recoverable.

### Concurrency anomalies

Take account A with ₹5,000:

Dirty read: T2 reads 4000, written by T1 but not committed, and then T1 rolls back to 5000. T2 has acted on a value that never existed. READ COMMITTED and above prevent it.

- Dirty read: T2 reads 4000, written by T1 but not committed, and then T1 rolls back to 5000. T2 has acted on a value that never existed. READ COMMITTED and above prevent it.
- Non-repeatable read: T1 reads A twice and gets 5000, then 4000, because T2 updated A and committed in between. Both values are committed; REPEATABLE READ prevents it.
- Phantom read: T1 runs the same count twice and gets 2, then 3, because T2 inserted a matching row and committed. No row T1 read changed; only SERIALIZABLE prevents it in the standard.

### Isolation levels

SQL defines four isolation levels by which of three phenomena they allow:

Defaults differ: MySQL's InnoDB uses REPEATABLE READ ; PostgreSQL, Oracle and SQL Server use READ COMMITTED . Implementations go beyond the table. InnoDB's REPEATABLE READ reads from a snapshot taken at the first read and uses next-key locks for locking reads, so phantoms are prevented in most cases; PostgreSQL treats READ UNCOMMITTED as READ COMMITTED.

The lost update is not in the standard table. SERIALIZABLE prevents it. At REPEATABLE READ, PostgreSQL aborts the second writer with a serialization error, while InnoDB lets a read-then-write in application code lose an update. Avoid it with an atomic UPDATE accounts SET balance = balance - 1000 , or by reading with SELECT … FOR UPDATE , which takes the write lock up front.

Most modern systems implement isolation with multi-version concurrency control (MVCC) : a write creates a new version of a row, and each reader sees the versions committed as of its snapshot, so readers never block writers and writers never block readers. Writers still lock rows against each other.

### Locks: shared and exclusive

A lock is a transaction's right to use an item. A shared lock (S) permits reading; an exclusive lock (X) permits reading and writing.

Locking alone does not give serializability: a transaction that unlocks A, then later locks B, can let another transaction see a mix of its old and new state. The protocol around the locks matters.

### Two-phase locking

Under two-phase locking (2PL) , each transaction has a growing phase , in which it may acquire locks but release none, then a shrinking phase , in which it may release locks but acquire none. The moment it acquires its last lock is its lock point . Every schedule 2PL allows is conflict serializable, in the order of the transactions' lock points.

Basic 2PL: T1 takes X(A) and X(B) as it needs them, and its lock point is X(B), its last acquisition. After the first unlock it may never lock again, which is what makes every 2PL schedule conflict serializable.

- Basic 2PL: T1 takes X(A) and X(B) as it needs them, and its lock point is X(B), its last acquisition. After the first unlock it may never lock again, which is what makes every 2PL schedule conflict serializable.
- Strict 2PL holds its exclusive locks until commit, so no other transaction can read or overwrite T1's uncommitted writes. An abort then never forces anyone else to roll back.

2PL fixes the lost update, but it can deadlock, as when two transactions both read a balance under a shared lock and then both try to upgrade it to write:

T1 wants to read the balance, so it asks for a shared lock on A. Nobody holds A: granted.

- T1 wants to read the balance, so it asks for a shared lock on A. Nobody holds A: granted.
- T2 asks for S(A) too. Shared locks are compatible with each other, so both transactions now hold S(A) and both read the same balance.
- T1 asks to upgrade to X(A) to write the new balance. X conflicts with T2's S, so T1 waits, and the wait-for graph gets the edge T1 → T2.
- T2 asks to upgrade to X(A) as well, and must wait for T1's shared lock. T2 waits for T1 and T1 waits for T2: a cycle in the wait-for graph, which is a deadlock. Neither can ever proceed.
- The DBMS finds the cycle and rolls back one victim, here T2. Its shared lock is released, T1's upgrade to X(A) is granted, and T2 restarts later. Taking X(A) at the first read, as SELECT … FOR UPDATE does, avoids this deadlock.

### Timestamp ordering

The timestamp-ordering protocol uses no locks. Each transaction gets a timestamp when it starts (smaller means older), and conflicting operations must happen in timestamp order. Each item X keeps R-TS(X) and W-TS(X), the largest timestamps of transactions that read and wrote it.

A rolled-back transaction restarts with a new timestamp. The protocol guarantees conflict serializability and is deadlock-free, since nobody waits, but long transactions can starve, and schedules are recoverable only if commits are handled carefully. With the Thomas write rule it also accepts some view-serializable schedules such as S3.

### Deadlock handling

A deadlock is a set of transactions each waiting for a lock held by another in the set. Systems handle it in three ways:

- Detection : keep a wait-for graph (Ti → Tj when Ti waits for a lock Tj holds); a cycle is a deadlock, and one victim is rolled back. InnoDB checks at once by default and rolls back the transaction it judges smallest, by rows changed.
- Timeout : give up after waiting too long (InnoDB's innodb_lock_wait_timeout , 50 seconds by default).
- Prevention with timestamps: wait-die and wound-wait, which let waits run in one direction only, so no cycle can form.

With T1 older (timestamp 5) and T2 younger (timestamp 10):

In both schemes the rolled-back transaction restarts with its original timestamp, so it eventually becomes the oldest and cannot starve. Wait-die can kill a young transaction repeatedly; wound-wait usually causes fewer rollbacks.

### Common mistakes

- Drawing a precedence edge for two reads: only read-write, write-read and write-write pairs conflict.
- Drawing edges from the later operation to the earlier: the edge follows time.
- Saying 2PL prevents deadlocks: it guarantees serializability, and deadlocks remain possible.
- Saying serializable means "serial": the transactions still interleave.
- Assuming REPEATABLE READ prevents lost updates everywhere: InnoDB allows them for read-then-write.
- Confusing timestamp restarts: timestamp ordering restarts with a new timestamp; wait-die and wound-wait keep the old one.

### Interview questions

What is the difference between conflict and view serializability? Conflict serializability requires reordering by swaps of non-conflicting operations and is tested with a precedence graph in polynomial time. View serializability only requires the same reads and final writes; it is a larger class, differing through blind writes, and testing it is NP-complete.

How do you check whether a schedule is conflict serializable? Build the precedence graph with an edge Ti → Tj for each conflicting pair where Ti's operation comes first. If there is no cycle, it is conflict serializable, and a topological sort gives the equivalent serial order.

Why does strict 2PL hold exclusive locks until commit? So that no other transaction can read or overwrite uncommitted data. That makes schedules strict, so an abort never forces other transactions to roll back.

Which anomalies does each isolation level prevent? READ COMMITTED prevents dirty reads, REPEATABLE READ also prevents non-repeatable reads, and SERIALIZABLE also prevents phantoms. READ UNCOMMITTED prevents none of the three.

How do databases detect deadlocks? They maintain a wait-for graph and look for cycles, either on every wait or periodically, then roll back a victim, usually the transaction cheapest to undo. Lock wait timeouts are a fallback.

What is MVCC and why is it used? Multi-version concurrency control keeps several committed versions of a row so each reader sees a consistent snapshot. Readers and writers do not block each other, which suits read-heavy workloads; InnoDB and PostgreSQL both use it.

What is a cascading rollback and how do you avoid it? When one transaction aborts, others that read its uncommitted writes must abort too, and so on. Cascadeless schedules, produced by strict 2PL, avoid it by letting transactions read only committed data.

Explain wait-die and wound-wait. Both give every transaction a timestamp. In wait-die, older transactions wait and younger ones requesting an older one's lock are rolled back; in wound-wait, older transactions pre-empt younger holders and younger ones wait.

Next, how a database finds rows quickly: Indexing and B+ Trees in DBMS . Isolation and transactions are examined in the SQL (Intermediate) skill test .

### What is a serializable schedule?

A schedule is serializable if its effect on the database equals that of some serial schedule, where the same transactions run one at a time. Conflict serializability, tested with a precedence graph, is the practical form: the schedule can be turned into a serial one by swapping adjacent non-conflicting operations.

### What is two-phase locking?

Two-phase locking (2PL) is a protocol in which each transaction acquires locks in a growing phase and releases them in a shrinking phase, never acquiring a lock after releasing any. It guarantees conflict-serializable schedules. Strict 2PL also holds exclusive locks until commit, which prevents cascading rollbacks.

### What is the difference between a dirty read and a non-repeatable read?

A dirty read reads a value written by a transaction that has not committed and may still roll back. A non-repeatable read reads the same row twice and gets different committed values because another transaction updated it in between. READ COMMITTED prevents the first; REPEATABLE READ prevents both.

### What is the default isolation level in MySQL?

InnoDB, MySQL's default storage engine, uses REPEATABLE READ by default. PostgreSQL, Oracle and SQL Server default to READ COMMITTED. You can change it per session with SET TRANSACTION ISOLATION LEVEL, for example SET TRANSACTION ISOLATION LEVEL READ COMMITTED.

### What is the difference between wait-die and wound-wait?

Both prevent deadlock using transaction timestamps, where older means a smaller timestamp. In wait-die an older transaction waits for a younger one, and a younger requester is rolled back. In wound-wait an older requester rolls the younger holder back, and a younger requester waits.

### What is a phantom read?

A phantom read happens when a transaction runs the same query twice and the second run returns extra or missing rows, because another transaction inserted or deleted rows matching the condition and committed in between. Only SERIALIZABLE prevents it under the SQL standard, though InnoDB's REPEATABLE READ prevents it in most cases.


---

## Module 11: Indexing and B+ Trees in DBMS

*Original URL: https://codekairo.com/notes/dbms/indexing-and-b-plus-trees*

### Overview

Quick answer

### What is indexing in DBMS?

An index is an auxiliary data structure that maps values of a column (the search key) to the rows that hold them, so the DBMS can find rows without scanning the whole table. Most relational databases use B+ tree indexes, which keep keys sorted in a balanced tree and answer equality and range queries in a few page reads; hash indexes answer only equality lookups.

- Why indexes
- Primary, clustering and secondary indexes
- Dense and sparse indexes
- Multilevel indexes
- B-tree vs B+ tree
- B+ tree structure
- Worked example: inserting into a B+ tree
- Searching
- Hash indexes
- The cost of an index
- Composite indexes and the leftmost-prefix rule
- Common mistakes
- Interview questions
- Common questions
- Test yourself

Finding one student among a million by reading every row is like finding a topic in a textbook by reading every page. An index is the book's index for a table: a separate, sorted structure that says where each value lives. With the right index a lookup touches a handful of disk pages instead of thousands. This note covers the kinds of index, dense and sparse and multilevel indexes, then the B+ tree that almost every relational database uses, with search and insertion worked step by step, and ends with hash indexes, the cost of indexes and the leftmost-prefix rule for composite ones.

### Why indexes

Databases read and write data in pages (blocks) of a fixed size: 16 KB in InnoDB, 8 KB in PostgreSQL. The cost of a query is roughly the number of pages it reads. Suppose a table of 1,000,000 students fits 100 rows to a page: that is 10,000 pages, and a query by roll number without an index reads all of them.

A B+ tree with a fan-out (children per node) of 100 and 100 keys per leaf needs only three levels for that table:

Each page of the tree points to 100 pages below it, so the levels hold 1, 100, 10,000 pages and the leaves reach 1,000,000 keys. A lookup reads one page per level and then the row's page: 4 reads instead of 10,000.

Real fan-outs are larger, often several hundred keys per 16 KB page for small keys, so three or four levels cover very large tables.

The terms: the search key is the column (or columns) an index is built on, which need not be a primary or candidate key. An index entry is a search-key value with a pointer to the row or the block holding it. Ordered indexes keep entries sorted (B+ trees); hash indexes spread them across buckets with a hash function.

### Primary, clustering and secondary indexes

In everyday database language the two words are clustered and non-clustered . A clustered index determines how the rows are physically ordered, so a table can have only one. In MySQL's InnoDB the table is a B+ tree on the primary key, with whole rows in its leaves. A secondary index in InnoDB stores (indexed value, primary key) in its leaves, so finding a row through it takes two tree walks: the secondary index to get the primary key, then the clustered index to get the row. If the secondary index already contains every column the query needs, the second walk is skipped; such an index is covering for that query, and EXPLAIN shows "Using index".

### Dense and sparse indexes

Take a data file sorted on roll_no, three records to a block, and look for 105 both ways:

The dense index has an entry for all 9 keys and points straight at 105. The sparse index has one entry per block, 3 in all: take the largest entry not above 105, 104, read block 2 and scan to 105.

A sparse index is smaller, but it needs the file sorted on the search key, which is why only a primary or clustering index can be sparse. A secondary index must be dense, because the rows are not in its order.

### Multilevel indexes

An index on a large table is itself large. If an inner index has 10,000 entries and 100 fit in a block, it spans 100 blocks, and binary search over them costs about ⌈log₂ 100⌉ = 7 block reads. Build a sparse outer index on the inner index, one entry per inner block: 100 entries, one block. Now a lookup reads the outer block, one inner block and the data block: 3 reads. Repeating the idea until the top level fits in one block gives a multilevel index . A B+ tree is a multilevel index that stays balanced automatically as rows are inserted and deleted.

### B-tree vs B+ tree

When a database's documentation says "B-tree index", it almost always means a B+ tree: InnoDB and PostgreSQL both use B+ trees.

### B+ tree structure

This note uses a B+ tree of order 4 : a node has at most 4 children and therefore at most 3 keys. Textbooks define "order" differently (maximum children, maximum keys, or minimum keys), so in an exam, state your convention. The rules:

- Every leaf is at the same depth: the tree is always balanced .
- An internal node with k keys has k + 1 children. Keys in child i are at least key i−1 and less than key i.
- Every node except the root is at least half full: internal nodes have 2 to 4 children, leaves 2 to 3 keys.
- Leaves hold every key (with its row or row pointer) and are linked left to right.

Splitting conventions used below. A leaf that overflows to 4 keys splits into two leaves of 2 keys each, and the first key of the right leaf is copied up into the parent (it must stay in the leaf too). An internal node that overflows to 4 keys keeps the first 2, moves the third up to its parent, and gives the fourth to a new right node.

### Worked example: inserting into a B+ tree

Insert 10, 20, 30, 40, 50, 15, 25, 35, 45, 55 into an empty order-4 B+ tree:

The tree starts as one leaf that is also the root. 10, 20, 30 fit, because an order-4 node holds at most 3 keys, kept sorted.

- The tree starts as one leaf that is also the root. 10, 20, 30 fit, because an order-4 node holds at most 3 keys, kept sorted.
- 40 belongs in the same leaf, which would then hold 4 keys, one more than the limit of 3. A node that overflows must split.
- The leaf splits into [10 20] and [30 40], and the right half's first key, 30, is copied up into a new root. It stays in the leaf too, because every key lives in a leaf; the root's copy is only a signpost.
- 50 ≥ 30, so it follows that pointer: [30 40 50] still has room, so 50 simply fits. Nothing above the leaf changes.
- 15 < 30, so it goes left: [10 15 20] still has room, so 15 simply fits. Nothing above the leaf changes.
- 25 makes a full leaf overflow, so it splits into [10 15] and [20 25] and copies 20 up: the parent becomes [20 30].
- 35 makes a full leaf overflow, so it splits into [30 35] and [40 50] and copies 40 up: the parent becomes [20 30 40], now full.
- 45 ≥ 40, so it follows that pointer: [40 45 50] still has room, so 45 simply fits. Nothing above the leaf changes.
- 55 lands in a full leaf, which splits into [40 45] and [50 55], copying 50 up. Now the root holds [20 30 40 50], 4 keys: it overflows too.
- An internal node splits differently: it keeps [20 30], moves 40 up into a new root and gives [50] to a new right node. 40 is moved, not copied, so it is no longer at that level. The tree grew at the top, so every leaf stays at the same depth.

The final tree has three levels: root [40]; internal nodes [20 30] and [50]; leaves [10 15] [20 25] [30 35] [40 45] [50 55], linked left to right. Check it against the rules: every leaf is at depth 3 and holds 2 or 3 keys, every internal node has 2 to 4 children (the root may have as few as 2), and 40 and 50 appear both as signposts and in leaves, because leaf splits copy keys up while the internal split moved 40 out of its node.

### Searching

A point lookup follows one pointer per level; a range query finds its first key the same way and then follows the leaf links:

Lookup 35: at the root, 35 < 40, so go left; at [20 30], 35 ≥ 30, so take the third pointer; the leaf [30 35] holds it. 3 page reads, one per level.

- Lookup 35: at the root, 35 < 40, so go left; at [20 30], 35 ≥ 30, so take the third pointer; the leaf [30 35] holds it. 3 page reads, one per level.
- Lookup 22 follows the same rules to the leaf [20 25] and finds no 22 there. A miss also costs exactly one read per level: every search ends at a leaf.
- Range 22 to 42: descend as for 22 to [20 25], then follow the leaf links right, collecting 25, 30, 35, 40, and stop at 45, the first key past 42. The tree is never climbed again.

The links are what make B+ trees good at BETWEEN , > and ORDER BY .

Deletion mirrors insertion: remove the key from its leaf; if the leaf falls below half full, borrow a key from a sibling or merge with it, and fix the parent's signposts. Merges can cascade up and shrink the tree by one level. Search, insertion and deletion each cost O(log n) page reads, where the base of the logarithm is the fan-out.

### Hash indexes

A hash index applies a hash function to the search key and stores the entry in the resulting bucket. An equality lookup ( WHERE email = '…' ) costs about one bucket read on average, independent of table size. But hashing destroys order, so a hash index cannot answer ranges, ORDER BY or prefix searches such as LIKE 'abc%' . Collisions go into overflow chains, and dynamic schemes (extendible and linear hashing) grow the table without rehashing everything.

In practice: MySQL's MEMORY engine supports explicit hash indexes; InnoDB uses B+ trees and builds an internal adaptive hash index over frequently used pages on its own; PostgreSQL offers CREATE INDEX … USING hash .

### The cost of an index

Indexes are not free:

- Writes : every INSERT and DELETE updates every index on the table, and an UPDATE updates each index containing a changed column, sometimes splitting pages.
- Space : each index is another tree on disk and competes for the buffer pool in memory.
- Choice : the optimizer may ignore an index that matches a large fraction of rows (low selectivity, such as a yes/no column), because a sequential scan is cheaper than thousands of random lookups.

Index the columns that appear in frequent WHERE , JOIN and ORDER BY clauses, check with EXPLAIN , and drop indexes nothing uses.

### Composite indexes and the leftmost-prefix rule

A composite index covers several columns, for example CREATE INDEX idx ON employees (dept, city, salary) . Its entries are sorted by dept, then by city within each dept, then by salary within each (dept, city), like names in a phone book sorted by surname then first name. So it can only seek on a leftmost prefix of its columns:

The index keeps its 9 entries sorted by dept, then city, then salary. dept = 'CSE' is a leftmost prefix, so its 4 entries sit together: one seek to the first, then read until dept changes.

- The index keeps its 9 entries sorted by dept, then city, then salary. dept = 'CSE' is a leftmost prefix, so its 4 entries sit together: one seek to the first, then read until dept changes.
- Equality on dept and city narrows the run to CSE, Pune, which is sorted by salary inside, so salary > 50000 is a range at its end: 2 entries, found by seeking on all three columns.
- city = 'Pune' skips the leading column. Its 6 entries are scattered through 3 separate runs, one per department, so the index offers no single range to seek and the query must scan.
- With dept = 'CSE' AND salary > 50000, city sits between them unused, so salary is not sorted inside the CSE run. The index seeks dept, then checks salary on each of the 4 entries and keeps 3.

MySQL 8.0.13 and later can sometimes use a skip scan for a condition on a non-leading column, but do not design around it. Put equality columns first and the range column last, and prefer the more selective equality column first when queries use both.

### Common mistakes

- Thinking a table can have several clustered indexes: it is stored in one order only.
- Indexing every column: writes slow down and most of the indexes are never used.
- Expecting an index on (a, b) to help WHERE b = … : it is not a leftmost prefix.
- Using a hash index for range queries or sorting: hashing destroys order.
- Forgetting that leaf splits copy the key up while internal splits move it.
- Wrapping an indexed column in a function, such as WHERE YEAR(joined) = 2025 : the B+ tree is sorted on the column, not the function, so the index cannot seek.

### Interview questions

What is an index and why does it speed up queries? A sorted (or hashed) structure from search-key values to rows. It replaces a full scan of every page with a walk down a tree of a few levels, so a lookup reads a few pages instead of thousands.

What is the difference between a B-tree and a B+ tree? A B-tree stores data pointers in every node; a B+ tree stores them only in linked leaves and uses internal keys purely as signposts. B+ trees have higher fan-out, shorter height and fast range scans, which is why databases use them.

What is the difference between a primary and a secondary index? A primary index is built on the key the file is sorted by and can be sparse; there is one per file. A secondary index is built on any other column, must be dense and can be added many times.

What is a covering index? An index that contains every column a query needs, so the query is answered from the index alone without reading the table rows. In InnoDB, a secondary index on (dept, salary) covers SELECT salary FROM employees WHERE dept = 'CSE' .

When will a database not use an index? When the condition is not on a leftmost prefix, when the column is wrapped in a function or compared with an implicit type conversion, when a LIKE pattern starts with % , or when so many rows match that a scan is cheaper.

What is the height of a B+ tree with fan-out 100 holding a million keys? About three levels, since 100³ = 1,000,000. Each lookup reads one page per level, so three index pages plus the row's page.

What happens when a B+ tree node overflows? It splits in two. A leaf copies its new right half's first key up to the parent; an internal node moves its middle key up. If the root splits, a new root is created and the tree grows by one level.

Why should the primary key of an InnoDB table be short? Every secondary index stores the primary key in each entry, so a long primary key makes every index larger. A short, increasing key such as an auto-increment integer also appends to the end of the clustered index instead of splitting pages in the middle.

Next, the databases that are not relational at all: SQL vs NoSQL Databases . Index design is examined in the SQL (Intermediate) skill test .

### What is the difference between a clustered and a non-clustered index?

A clustered index decides the physical order of the rows: the table itself is stored sorted by its key, so there can be only one. A non-clustered (secondary) index is a separate structure whose entries point to the rows. In MySQL's InnoDB the primary key is the clustered index, and secondary index entries store the primary key value.

### Why do databases use B+ trees instead of binary search trees?

A binary search tree node holds one key, so a million keys need about 20 levels, each a separate disk read. A B+ tree node is a whole disk page holding hundreds of keys, so the same million keys fit in about three levels. The tree stays balanced, and linked leaves make range scans fast.

### What is the difference between a dense and a sparse index?

A dense index has an entry for every search-key value in the file. A sparse index has entries for only some values, typically the first key of each data block, and works only when the file is sorted on that key. Sparse indexes are smaller; dense ones can answer whether a value exists without reading the data.

### What is the leftmost prefix rule?

A composite index on (a, b, c) is sorted by a, then by b within a, then by c. So it can seek on a, on a and b, or on a, b and c, but not on b or c alone. A range condition on one column also stops the columns after it being used for seeking.

### Do indexes slow down inserts and updates?

Yes. Every INSERT and DELETE must also change every index on the table, and an UPDATE must change each index that contains a modified column, sometimes splitting pages. Indexes also take disk space and buffer memory. Add an index for queries that need it, not for every column.


---

## Module 12: SQL vs NoSQL Databases

*Original URL: https://codekairo.com/notes/dbms/sql-vs-nosql*

### Overview

Quick answer

### What is the difference between SQL and NoSQL databases?

SQL (relational) databases store data in tables with a fixed schema, link them with keys and joins, and give multi-row ACID transactions; MySQL and PostgreSQL are examples. NoSQL databases use other models (documents, key-value pairs, wide columns or graphs) with flexible schemas and built-in horizontal scaling, often trading joins and strict consistency for scale; MongoDB, Redis, Cassandra and Neo4j are examples.

- The relational model
- The NoSQL families
- SQL vs NoSQL
- ACID vs BASE
- The CAP theorem
- Replication
- Sharding
- When to choose which
- Common mistakes
- Interview questions
- Common questions
- Test yourself

For decades "database" meant a relational database queried with SQL. In the 2000s, web companies needed to store more data, across more machines, with less rigid structure than one relational server handled comfortably, and a family of non-relational systems grew up under the name NoSQL (now read as "not only SQL"). Interviewers ask about the trade-offs: when a document or key-value store beats a table, what ACID and BASE mean, and what the CAP theorem really says. This note answers those, and covers replication and sharding, the two techniques behind every distributed database.

### The relational model

A relational database stores data in tables with a schema declared in advance (schema-on-write). Tables are linked by keys, queries combine them with joins, constraints keep the data valid, and transactions are ACID across any number of rows and tables. MySQL, PostgreSQL, Oracle Database and SQL Server are the common ones. Its strengths are exact, flexible querying (any question the data can answer, written in SQL) and integrity. Its traditional weakness is scaling writes beyond one machine, which is possible but not built in.

The previous notes describe this model: keys , normalization , joins and transactions .

### The NoSQL families

Here is the same idea, a customer and her orders, in each model:

Relational: the customer, her 2 orders and their 3 items go into three tables linked by keys, each fact stored once. Showing her profile with orders takes two joins.

- Relational: the customer, her 2 orders and their 3 items go into three tables linked by keys, each fact stored once. Showing her profile with orders takes two joins.
- Document: the orders and their items are embedded inside the customer, so one read of 162 bytes returns everything the profile page needs. Data another document also needs would have to be copied into it.
- Key-value: the store knows only keys and the bytes stored under them. GET customer:101 is one very fast lookup, but "orders above ₹1,000" cannot be asked: the store cannot look inside a value.
- Wide-column: customer_id is the partition key, so all of Asha's orders live together on the same nodes, sorted by the clustering columns, newest first. Reading her latest orders is one sequential read; the table exists for that one query.
- Graph: Asha, her orders and the products are nodes, and each relationship is a stored edge. A question that follows relationships, such as which products she bought, walks edges from her node instead of joining tables.

Document (MongoDB), as stored:

```
{
"_id"
:
101
,
"name"
:
"Asha"
,
"city"
:
"Pune"
,
"orders"
:
[
{
"order_id"
:
9001
,
"total"
:
1499
,
"items"
:
[
"keyboard"
]
}
,
{
"order_id"
:
9002
,
"total"
:
299
,
"items"
:
[
"mouse pad"
,
"cable"
]
}
]
}
```

Embedding is fast to read but duplicates data that other documents also need, which is denormalization with the usual update anomalies.

Key-value (Redis): the database knows only keys. Values can be strings, or in Redis's case lists, hashes and sorted sets, and keys can expire.

```
SET cart:101 "{\"items\": 3, \"total\": 1798}" EX 3600
GET cart:101
```

Wide-column (Cassandra): you design one table per query. Here the partition key customer_id decides which nodes store the rows, and the clustering columns keep each customer's orders sorted newest first inside the partition.

```
CREATE TABLE orders_by_customer (
  customer_id int,
  order_date  date,
  order_id    int,
  total       int,
  PRIMARY KEY ((customer_id), order_date, order_id)
) WITH CLUSTERING ORDER BY (order_date DESC, order_id DESC);
```

Graph (Neo4j, Cypher query language): relationships are stored as edges, so "what did Asha's friends buy?" is a traversal, not a chain of joins.

```
MATCH (a:Customer {name: 'Asha'})-[:FRIEND]->(f)-[:BOUGHT]->(p:Product)
RETURN DISTINCT p.name
```

### SQL vs NoSQL

The line has blurred. PostgreSQL and MySQL store and index JSON; MongoDB has multi-document transactions; Cassandra speaks the SQL-like CQL; and distributed SQL databases such as Google Spanner, CockroachDB and TiDB scale horizontally with ACID transactions. Choose by the workload, not the label.

### ACID vs BASE

ACID puts correctness first. BASE describes many distributed NoSQL stores:

- Basically available : the system answers every request, even during failures, possibly with stale data.
- Soft state : the state can change without new input, as replicas exchange updates.
- Eventually consistent : if updates stop, all replicas converge to the same value.

### The CAP theorem

Eric Brewer conjectured it in 2000, and Seth Gilbert and Nancy Lynch proved it in 2002. Its three properties have precise meanings:

- Consistency (C) : every read returns the most recent write or an error, as if there were one copy of the data (linearizability).
- Availability (A) : every request received by a non-failing node gets a non-error response.
- Partition tolerance (P) : the system keeps operating when the network drops messages between nodes.

The theorem: if a network partition occurs, a distributed system must choose between consistency and availability. It cannot guarantee both while nodes cannot talk to each other.

Two replicas of the same data, in Mumbai and Singapore. While the link works, a write to Mumbai (likes = 42) is copied to Singapore, and both answer alike.

- Two replicas of the same data, in Mumbai and Singapore. While the link works, a write to Mumbai (likes = 42) is copied to Singapore, and both answer alike.
- The link fails: a partition. A new write reaches Mumbai, which now holds 43, but cannot be copied, so Singapore still holds 42. Now a read arrives in Singapore.
- A CP choice keeps consistency: Singapore cannot confirm it has the latest value, so it refuses the read with an error until the link is back. Everyone who gets an answer gets the latest one.
- An AP choice keeps availability: Singapore answers with what it has, 42, which is stale. Every request gets an answer, and some answers are out of date.
- When the link returns, the AP replicas exchange updates and converge on 43: eventual consistency. CAP's choice only bites during a partition; with the link up, a system can be both consistent and available.

The popular "pick any two of three" is misleading. Partitions are not optional in a distributed system, so you cannot "choose CA" by giving up P; a CA system is simply one that is not distributed, such as a single database server. When there is no partition, a system can be both consistent and available. The PACELC refinement (Daniel Abadi, 2012) adds the everyday trade-off: if there is a P artition, choose A or C ; E lse, choose lower L atency or C onsistency.

Many databases are tunable, so classify a configuration rather than a product. Cassandra with consistency level ONE behaves as AP; with QUORUM reads and writes it leans towards consistency. MongoDB with majority read and write concerns behaves as CP. Also note that CAP's C is not ACID's C : ACID's consistency means constraints hold, while CAP's means replicas agree.

### Replication

Replication keeps copies of the same data on several nodes, for fault tolerance and to spread reads.

- Leader-follower (primary-replica): all writes go to the leader, which streams changes to followers; reads may go to any. MySQL replication, PostgreSQL streaming replication and MongoDB replica sets work this way.
- Synchronous or asynchronous : a synchronous leader waits for a follower to confirm each write, so failover loses nothing but writes are slower; an asynchronous one does not wait, so followers lag and a failover can lose the latest writes.
- Replication lag can break read-your-writes: a user's next read, served by a follower that is behind, may not show her own change.
- Multi-leader accepts writes in several places (for example one leader per data centre) and must resolve conflicting writes.
- Leaderless (Dynamo-style, as in Cassandra): a client writes to W of the N replicas and reads from R of them. If R + W > N, every read set overlaps every write set.

The user renames her profile to "Asha Patel". The write goes to the leader, which acknowledges it and streams it to the followers without waiting: follower 1 has applied it, follower 2 has not yet.

- The user renames her profile to "Asha Patel". The write goes to the leader, which acknowledges it and streams it to the followers without waiting: follower 1 has applied it, follower 2 has not yet.
- The next page load is a read, sent to follower 2, which still shows "Asha". The user's own change seems to have vanished, though it is safe on the leader.
- A common fix: for a short while after a user writes, read that user's own data from the leader. Everyone else's reads can still go to any follower.

The quorum rule of leaderless stores, checked over every possible read:

A write of v2 waits for W = 2 of the 3 replicas. With R = 2, all 3 possible read sets share at least one replica with the write set, because 2 + 2 > 3: every read sees v2 and keeps the newest version.

- A write of v2 waits for W = 2 of the 3 replicas. With R = 2, all 3 possible read sets share at least one replica with the write set, because 2 + 2 > 3: every read sees v2 and keeps the newest version.
- With R = 1, R + W = 3 is not greater than 3: a read that happens to ask only replica 3 gets the old v1. The overlap rule, not the number of copies, is what makes reads current.

### Sharding

Sharding (horizontal partitioning) splits the rows of one data set across nodes by a shard key , so each node stores and serves only its part. It spreads data volume and write load, which replication alone cannot.

By range, each shard holds a contiguous run of ids. A range query for 1005–1008 (blue) stays on one shard, but every new order, 1010, 1011, 1012 (solid), lands on the last shard: a hot spot.

- By range, each shard holds a contiguous run of ids. A range query for 1005–1008 (blue) stays on one shard, but every new order, 1010, 1011, 1012 (solid), lands on the last shard: a hot spot.
- By hash, each id goes to shard (FNV-1a hash of the id) mod 3. The new orders spread over 3 shards, but neighbouring ids are scattered, so the same range query must ask every shard.

A good shard key has many distinct values, spreads reads and writes evenly, and keeps data that is queried together on one shard. The costs are real: joins and transactions across shards are slow or unsupported, and rebalancing moves data while the system runs. Relational databases can be sharded too, with tools such as Vitess for MySQL and Citus for PostgreSQL. Vertical scaling (a bigger machine) is simpler and should usually come first; horizontal scaling (more machines) is what sharding enables.

### When to choose which

Many systems use several stores at once (polyglot persistence): a relational database as the source of truth for accounts and orders, Redis in front of it as a cache, perhaps a search engine beside it. The practical default is a relational database until a measured need points elsewhere.

### Common mistakes

- Reading CAP as "pick two of three": partitions are unavoidable, so the choice is C or A during a partition.
- Equating CAP's consistency with ACID's consistency.
- Saying NoSQL databases have no transactions: many offer single-record atomicity, and some offer multi-record ACID transactions.
- Saying SQL databases cannot scale horizontally: replicas, sharding tools and distributed SQL all exist.
- Confusing replication with sharding: copies of the same data versus different parts of the data.
- Choosing NoSQL for "flexible schema" and then needing joins and integrity everywhere.

### Interview questions

What does NoSQL stand for, and what are its main types? It is now read as "not only SQL", a name for non-relational databases. The main types are document, key-value, wide-column and graph stores.

State the CAP theorem correctly. In the presence of a network partition, a distributed system cannot be both consistent (linearizable) and available. It must refuse some requests to stay consistent, or answer them with possibly stale data to stay available.

Is Cassandra CP or AP? It is usually described as AP, because it keeps accepting reads and writes during partitions and converges later. But consistency is tunable per query, and QUORUM reads with QUORUM writes give much stronger guarantees, so it depends on configuration.

What is the difference between vertical and horizontal scaling? Vertical scaling adds CPU, memory or disk to one machine; it is simple but bounded and keeps one point of failure. Horizontal scaling adds machines and spreads data and load across them through replication and sharding.

How do you choose a shard key? Pick a column with many distinct values and even access, used by most queries to find data, so that each query hits one shard and no shard runs hot. User id is a common choice; a timestamp alone is a classic hot-spot mistake.

What is R + W > N in leaderless replication? With N replicas, a write waits for W acknowledgements and a read queries R replicas. If R + W > N the two sets must share at least one replica, so a read sees the latest acknowledged write.

Would you store a bank's transactions in MongoDB or MySQL? In a relational database such as MySQL or PostgreSQL by default, because transfers need multi-row ACID transactions, constraints and strong consistency. A document store could work with multi-document transactions, but it gives up the strengths it is chosen for.

Why might a social network use a graph database? Queries such as friends of friends or people you may know follow edges several hops deep. A graph database stores the edges directly, so each hop is a pointer lookup, whereas a relational database needs one self-join per hop.

You have reached the end of the DBMS notes. Go back to the start with Introduction to DBMS , browse the DBMS notes , or test yourself with the SQL (Basic) and SQL (Intermediate) skill tests.

### What is the CAP theorem?

The CAP theorem says that when a network partition splits a distributed database, it must give up either consistency (every read sees the latest write) or availability (every request to a working node gets a non-error answer). Partitions cannot be ruled out, so the real choice is what a system does during one.

### What is the difference between ACID and BASE?

ACID (atomicity, consistency, isolation, durability) puts correctness first: a committed transaction is complete, valid and immediately visible to all. BASE (basically available, soft state, eventually consistent) puts availability first: the system keeps answering, replicas may briefly disagree, and they converge once updates stop. Relational databases follow ACID; many distributed NoSQL stores follow BASE.

### Is MongoDB ACID compliant?

Partly by default and fully when asked. A write to a single document has always been atomic. Since version 4.0 MongoDB supports multi-document ACID transactions on replica sets, and since 4.2 on sharded clusters. Its consistency guarantees also depend on the read and write concerns you choose.

### What is the difference between sharding and replication?

Replication keeps copies of the same data on several nodes, for availability and to spread reads. Sharding splits the data so each node holds a different part, to spread storage and writes. Large systems use both: the data is sharded, and each shard is replicated.

### When should you use NoSQL instead of SQL?

When a specific need outgrows what a relational database does comfortably: very high write volumes across many machines, data accessed as whole documents with changing fields, key lookups at very low latency, or deep relationship traversals. For structured data with transactions and integrity rules, a relational database is the usual default.

### What is eventual consistency?

Eventual consistency guarantees that if no new updates are made to an item, all replicas will eventually return the same value. Until then, different replicas may answer with different versions, so a user can briefly see an old like count or a deleted comment. It is the price of staying available during failures.


---

