---
permalink: /core-concepts/
layout: home
title: Core Concepts
---

# Core Concepts<i class="fas fa-graduation-cap m-2"></i>
--------------------------------------------------------------------------------------------------------------

Welcome to Stackzilla Core Concepts. Consider this your Stackzilla 101 introductory course. By the end of this guide, you should be familiar with what problems Stackzilla solves, how Stackzilla works, and where to go next.


## Terminology<i class="fal fa-spell-check m-2"></i>
--------------------------------------------------------------------------------------------------------------
Before diving into the core concepts, let's level-set with the lexicon. Ensuring thatm, I the writer, and you the reader, are on the same page - is kind of a big deal.

| Term         | Definition |
|--------------|------------|
| Blueprint | One or more Python files which contain **Resources** |
| Resource | A Python class that models an object managed by Stackzilla |
| Attribute | Python class variable, which is a property of a **Resource** |
| Namespace | A database which contains information about a deployed **Blueprint** |
| Metadata | Collection of Key-Value pairs housed within a **Namespace** |
| Provider | Base `class` which *provides* the template and logic for a **Resource** |
| Dependency | A **Resource** which must be deployed prior to another **Resource** |
| Deployed | The process of Stackzilla creating, configuring, or otherwise applying a **Resoruce** |

## What Would You Say, You Do Here?<i class="fad fa-dragon m-2"></i>
--------------------------------------------------------------------------------------------------------------
Stackzilla is an *Application ORM*. Far more than just *infrastructure as code*, Stackzilla provides Python developers (that's you!) with an intuitive ORM for defining and deploying both their application infrastucture **AND** their aplication.

The basic Stackzilla lifecycle:
- Write a **Blueprint**: A collection of Python class(es) for the **Resources** in your application
- Execute `stackzilla blueprint apply`. **Providers** will use your code to **deploy** **Resources**
- Make changes to your **Blueprint** files and run `stackzilla blueprint apply` to keep the **deployed Resources** in sync.
- Execute `stackzilla blueprint delete` to delete all **Blueprint Resources** from the environment.


## Let's Talk Turkey<i class="fas fa-turkey m-2"></i>
We're all developers here, right? Let's talk insider baseball for a bit and go over how Stackzilla actually works.

### Providers
A Stackzilla **Provider** is a base class which inherits from `StackzillaResource`. All **Providers** have the ability to create, delete, and update whatever it is they are *providing*. For example, the AWS EC2 Instance **Provider** will have all of the logic to provision, update, and destroy a piece of compute on AWS.

### Blueprints
A **Blueprint** is simply a collection of Python modules, of which contain classes. Stackzilla is able to search through your blueprint, looking for classes which inherit from a **Provider**. These are what Stackzilla considers a **Resource**. Each time a `blueprint apply` is run, Stackzilla will compare what is *on disk* to the last known state in the **Namespace** databse. Stackzilla reconciles those differences by having the **Provider** either create, update, or delete the **Resource**.

### It's All Just Python
The beauty of Stackzilla **Blueprints** is that there is no secret sauce. *It's Just Python!* If you want to inject custom logic at any point during the application process, simply override the desired method, and execute your logic. Want to create a **Resource** class on the fly, and inject it into the dependency chain? Go for it! Are your configuration variabled stored in a custom in-house database? Not a problem - write a function to fetch them and set the attribute with your function.

## Next Steps<i class="far fa-hand-point-right m-2"></i>
With a (hopefully) firm understanding of Stackzilla in hand, it's time to continue your learning.

<div class=row>
<div class="card text-white bg-primary m-1" style="max-width: 18rem;">
  <div class="card-header">Can we build it? <i class="fal fa-user-hard-hat"></i></div>
  <div class="card-body d-flex flex-column">
    <h5 class="card-title">Write a Blueprint</h5>
    <p class="card-text">Write Python code to define your applicaiton infrastructure and how it's deployed.</p>
    <p class="card-text text-center text-dark mt-auto"><a class="btn btn-light" href='{{ "/write-a-blueprint/" | relative_url }}'>Get Started</a></p>
  </div>
</div>

<div class="card text-white bg-secondary m-1" style="max-width: 18rem;">
  <div class="card-header">Become A Code Monkey. <i class="fal fa-monkey"></i></div>
  <div class="card-body d-flex flex-column">
    <h5 class="card-title">Contribute To Stackzilla</h5>
    <p class="card-text">Be an open source hero! Write code for the Stackzilla core project.</p>
    <p class="card-text text-center text-dark mt-auto"><a class="btn btn-light disabled">Get Started</a></p>
  </div>
</div>

<div class="card text-white bg-success m-1" style="max-width: 18rem;">
  <div class="card-header">Make it so. <i class="fal fa-starship"></i></div>
  <div class="card-body d-flex flex-column">
    <h5 class="card-title">Write A Provider</h5>
    <p class="card-text">Develop Stackzilla provider libraries for other developers to use in their blueprints.</p>
    <p class="card-text text-center text-dark mt-auto"><a class="btn btn-light disabled">Get Started</a></p>
  </div>
</div>

</div>
