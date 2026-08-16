"""NexusEnroll -- University Course Enrolment System (proof of concept).

SCS 2303 Software Architecture, Assignment 3.

Architecture:  Microservices (system level) + 3-Tier (inside each service).
               This package is the BUSINESS LOGIC LAYER -- tier 2 -- which is
               what the brief asks Part B to focus on.

Layout:
    domain/        business entities (diagram 02)
    patterns/      the seven design patterns (diagram 03)
    repositories/  interfaces owned by the business layer + in-memory impls
    services/      the student, faculty and administrator modules
    seed.py        demo data
    composition_root.py   the single place objects are wired (replaces Singleton)
    main.py        runnable user stories
"""

__version__ = "1.0.0"
