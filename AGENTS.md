AI Coding Agent Instructions for Team Challenge Tracker

1. Project Summary

This project is a web application that helps groups of friends track shared challenges and keep each other accountable.

Users can:

create accounts

join public teams

participate in challenges

log daily check-ins

view a scoreboard

comment on activities

interact socially

The project is intentionally simple and server-rendered.

Do not introduce unnecessary complexity.

2. Technology Stack

Backend

Python

Flask

SQLAlchemy

WTForms

Flask-Migrate

Frontend

Jinja2 templates

Bootstrap 5

Database

PostgreSQL preferred

SQLite acceptable for development

Auth

email + password

Flask-Login

No frontend frameworks.

No REST API required for MVP.

Dependencies

Use `pip`

Maintain a `requirements.txt` file

3. Design Philosophy

When implementing code:

Prefer

simple functions

readable code

explicit logic

server-side rendering

Avoid

complex abstractions

microservices

unnecessary JavaScript

premature optimization

If unsure, choose the simplest implementation.

4. Core Product Concepts
Users
People with accounts.

Teams
Public groups users can join.

Non-members can see only a team's public summary:
name and description.

Challenges and other team internals are visible only to team members.

Challenges
Activities within teams.

Activities
Daily check-ins.

Scoreboard
Ranking of users by activity count.

Comments
Discussion on activities and challenges.

5. Key Rules

These rules are critical.

Users can join multiple teams.

Teams are public.

Users can freely join teams.

Non-members may view a team's name and description, but cannot view its internal challenge content until they join.

Users can freely join challenges.

One check-in per user per challenge per day.

Users can edit or backfill activities.

Scoreboard is based on total check-ins.

Database constraints must enforce rule #5.

6. Database Schema
users

id
email (unique)
password_hash
display_name
created_at
updated_at

teams

id
name
slug (unique)
description
created_by_user_id
created_at
updated_at

team_memberships

id
team_id
user_id
joined_at

Unique:
(team_id, user_id)

challenges

id
team_id
title
description
start_date
end_date
frequency_per_week
created_at
updated_at

challenge_memberships

id
challenge_id
user_id
joined_at

Unique:
(challenge_id, user_id)

activities

id
challenge_id
user_id
activity_date
is_checked
note
created_at
updated_at

Unique:
(challenge_id, user_id, activity_date)

Purpose:
Daily check-in.

activity_comments

id
activity_id
user_id
body
created_at
updated_at

challenge_comments

id
challenge_id
user_id
body
created_at
updated_at

7. Relationships

User
    - teams
    - challenges
    - activities
    - comments

Team
    - members
    - challenges

Visibility rule
    - non-members can see only team summary information
    - members can see team internals such as challenges

Challenge
    - activities
    - members
    - comments

Activity
    - comments

8. Scoreboard Logic

For a challenge:

score = number of activities

Where

is_checked = true

activity_date between start_date and end_date

Sort descending.

9. Activity Feed

Show most recent activities with:

user
date
note
comments

Newest first.

10. URL Structure

Auth

/register
/login
/logout

Teams

/teams
/teams/<slug>
/teams/<slug>/join

Challenges

/challenges/create
/challenges/<id>
/challenges/<id>/join

Activities

/challenges/<id>/checkin
/activity/<id>/edit

Comments

/activity/<id>/comment
/challenges/<id>/comment

11. Implementation Strategy

The agent should work in small steps and complete phases sequentially.
Do not attempt the whole project at once.

Phase 1 – Project Setup

Create:

Flask app
SQLAlchemy setup
Base template
User model
Authentication

Success condition:

User can register and login.

Phase 2 – Teams

Implement:

Team model
Membership model
Team pages
Join team
Restrict team internals so non-members only see the team summary and join option

Success condition:

Users can join teams.

Phase 3 – Challenges

Implement:

Challenge model
Join challenge
Challenge page

Success condition:

Users can join challenges.

Phase 4 – Activities

Implement:

Daily check-in
Edit activity
Backfill support

Success condition:

User can log activity.

Phase 5 – Scoreboard

Implement ranking query.

Success condition:

Challenge page shows ranking.

Phase 6 – Comments

Implement comments on:

activities
challenge feed

Success condition:

Users can comment.

12. Coding Conventions

Use:

Flask Blueprints

SQLAlchemy models

WTForms validation

Flask-Migrate for database migrations

Flask-Login for session authentication

A single config file for application configuration

Avoid:

inline SQL

global variables

large view functions

Break logic into helpers.

13. Suggested Project Structure
app
 ├── __init__.py
 ├── config.py
 ├── models.py
 ├── extensions.py

 ├── auth
 ├── teams
 ├── challenges
 ├── activities
 ├── comments

templates
static
migrations
14. When Modifying Code

Agents must:

Read existing code first.

Prefer modifying existing files.

Avoid creating duplicate utilities.

Keep changes minimal and clear.

15. Testing Strategy (optional but recommended)

Basic tests:

user registration

team join

challenge join

check-in constraint

scoreboard query

16. Non-Goals

Do not implement:

notifications

mobile apps

APIs

admin roles

private teams

analytics

advanced challenge types

17. Future Extensions

These features may be added later:

streak tracking

push notifications

mobile support

Design code so these can be added later.

19. Production and Hardening Notes

Current production/runtime setup now includes:

- Dockerfile and docker-compose for app + MySQL deployment
- Gunicorn for production serving
- `.env.production` / `.env.production.example` for environment configuration
- compose mapping `7050:7000`

Current anti-bot hardening now includes:

- Flask-Limiter on register/login auth routes
- Registration honeypot field
- Google reCAPTCHA on registration

Current implemented extensions:

- Team aggregate scoreboard (team page, across all team challenges)
- Activity emoji reactions with dropdown chooser
- Team challenge internals still hidden from non-members
- Docker production path for MySQL-backed runtime

18. Guidance for AI Coding Agents

When implementing features:

Implement database model first.

Add migration.

Add forms.

Add routes.

Add templates.

Follow this order.

If unclear, ask for clarification rather than guessing.

Project defaults confirmed:

- Use `pip` for dependency management
- Store dependencies in `requirements.txt`
- Use `Flask-Migrate` for migrations
- Use `Flask-Login` for authentication session management
- Use a single config file

End of file
