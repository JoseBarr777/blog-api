from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from datetime import datetime, timedelta
import random
from faker import Faker

from post.models import Post, PostStatus


class Command(BaseCommand):
    help = 'Generate test posts for API testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=25,
            help='Number of posts to create (default: 25)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing posts before creating new ones'
        )

    def handle(self, *args, **options):
        fake = Faker()
        
        if options['clear']:
            self.stdout.write('Clearing existing posts...')
            Post.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All posts cleared.'))

        # Create test users if they don't exist
        authors = []
        author_data = [
            ('john_blogger', 'john@example.com', 'John', 'Doe'),
            ('jane_writer', 'jane@example.com', 'Jane', 'Smith'),
            ('mike_author', 'mike@example.com', 'Mike', 'Johnson'),
            ('sarah_editor', 'sarah@example.com', 'Sarah', 'Wilson'),
            ('alex_creator', 'alex@example.com', 'Alex', 'Brown'),
        ]
        
        for username, email, first_name, last_name in author_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'password': 'testpass123'
                }
            )
            authors.append(user)
            if created:
                self.stdout.write(f'Created user: {username}')

        # Blog post topics and templates
        tech_titles = [
            "Getting Started with Django REST Framework",
            "Python Best Practices for Web Development",
            "Understanding Database Optimization",
            "Building Scalable APIs with Django",
            "JavaScript Modern Development Techniques",
            "Docker for Python Developers",
            "Testing Strategies for Web Applications",
            "React Component Design Patterns",
            "PostgreSQL Performance Tuning Guide",
            "CI/CD Pipeline Implementation",
        ]
        
        general_titles = [
            "The Future of Remote Work Technology",
            "Digital Transformation in Small Business",
            "Cybersecurity Best Practices for Teams",
            "Data Privacy in the Modern Web",
            "Open Source Software Benefits",
            "Cloud Computing Cost Optimization",
            "Mobile App Development Trends",
            "AI and Machine Learning Applications",
            "Blockchain Technology Explained",
            "Software Architecture Principles",
        ]
        
        tutorial_titles = [
            "How to Build a REST API Tutorial",
            "Step-by-Step Django Project Setup",
            "Creating Interactive Web Forms",
            "Database Migration Best Practices",
            "Setting Up Development Environment",
            "Git Workflow for Team Projects",
            "Debugging Python Applications",
            "Code Review Process Implementation",
            "Automated Testing Setup Guide",
            "Performance Monitoring Setup",
        ]

        all_titles = tech_titles + general_titles + tutorial_titles
        
        # Content templates
        content_templates = [
            """In today's rapidly evolving tech landscape, understanding {topic} has become more crucial than ever. 

This comprehensive guide will walk you through the essential concepts and practical implementations that every developer should know.

## Key Benefits

The main advantages of implementing {topic} include:
- Improved performance and efficiency
- Better code maintainability
- Enhanced user experience
- Scalable architecture design

## Implementation Steps

Here's how to get started:

1. **Planning Phase**: Begin by analyzing your current setup and identifying areas for improvement.
2. **Setup**: Configure your development environment with the necessary tools and dependencies.
3. **Implementation**: Follow best practices while implementing the core functionality.
4. **Testing**: Ensure thorough testing at each stage of development.
5. **Deployment**: Deploy your solution using industry-standard practices.

## Best Practices

When working with {topic}, keep these guidelines in mind:
- Always prioritize security considerations
- Maintain clean and readable code
- Document your implementation thoroughly
- Follow established coding standards
- Regular code reviews and testing

## Conclusion

Mastering {topic} will significantly improve your development workflow and help you build more robust applications. Remember to stay updated with the latest developments in this area.""",

            """The world of web development is constantly changing, and {topic} represents one of the most significant advances in recent years.

## Introduction

Whether you're a seasoned developer or just starting your journey, understanding {topic} is essential for modern web development.

## Core Concepts

Let's dive into the fundamental principles:

### Architecture
The underlying architecture focuses on modularity and reusability, making it easier to maintain and scale applications.

### Performance
Optimized performance is achieved through efficient algorithms and careful resource management.

### Security
Security considerations are built into the core design, ensuring robust protection against common vulnerabilities.

## Real-World Applications

Here are some practical use cases:

- **Enterprise Applications**: Large-scale business solutions benefit from the scalability and reliability.
- **Startup Projects**: Quick prototyping and development cycles are supported.
- **Educational Platforms**: Learning management systems can leverage these features effectively.

## Getting Started

To begin implementing {topic}:

1. Set up your development environment
2. Install required dependencies
3. Configure basic settings
4. Create your first implementation
5. Test thoroughly
6. Deploy to production

## Tips and Tricks

Pro tips from experienced developers:
- Start small and iterate
- Focus on user experience
- Optimize for performance early
- Maintain comprehensive documentation

The future looks bright for developers who embrace {topic} and integrate it into their development process.""",

            """Exploring {topic} opens up new possibilities for developers looking to enhance their skills and build better applications.

## Why {topic} Matters

In the competitive landscape of software development, staying ahead means adopting proven methodologies and tools that deliver results.

## Technical Overview

### Components
The system consists of several interconnected components:
- Core processing engine
- Data management layer
- User interface framework
- API integration services

### Workflow
The typical workflow involves:
1. Data input and validation
2. Processing and transformation
3. Output generation and formatting
4. Result delivery and storage

## Implementation Guide

### Prerequisites
Before starting, ensure you have:
- Basic understanding of web development
- Familiarity with relevant programming languages
- Access to development tools
- Test environment setup

### Step-by-Step Process
Follow these detailed steps:

**Phase 1: Planning**
- Define project requirements
- Create technical specifications
- Establish timelines and milestones

**Phase 2: Development**
- Set up project structure
- Implement core functionality
- Add supporting features

**Phase 3: Quality Assurance**
- Unit testing
- Integration testing
- Performance testing
- Security auditing

**Phase 4: Deployment**
- Production environment setup
- Deployment automation
- Monitoring and logging

## Troubleshooting

Common issues and solutions:
- Configuration errors: Check environment variables
- Performance bottlenecks: Profile and optimize code
- Integration problems: Verify API compatibility

## Advanced Topics

For experienced developers:
- Custom extensions and plugins
- Advanced configuration options
- Performance optimization techniques
- Scalability considerations

This comprehensive approach to {topic} will help you build robust, maintainable, and scalable applications."""
        ]

        created_count = 0
        
        for i in range(options['count']):
            # Random title
            title = random.choice(all_titles)
            if random.random() < 0.3:  # 30% chance to add variation
                title = f"{title} - {fake.catch_phrase()}"
            
            # Generate unique slug
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Random content
            topic = fake.bs().title()
            content = random.choice(content_templates).format(topic=topic)
            
            # Add some randomness to content length
            if random.random() < 0.3:
                content += f"\n\n## Additional Notes\n\n{fake.text(max_nb_chars=500)}"
            
            # Random author
            author = random.choice(authors)
            
            # Random status (70% published, 30% draft)
            status = PostStatus.PUBLISHED if random.random() < 0.7 else PostStatus.DRAFT
            
            # Random date within last 6 months
            end_date = timezone.now()
            start_date = end_date - timedelta(days=180)
            
            random_date = fake.date_time_between(
                start_date=start_date,
                end_date=end_date,
                tzinfo=timezone.get_current_timezone()
            )
            
            # Create post
            post = Post.objects.create(
                title=title,
                slug=slug,
                body=content,
                author=author,
                status=status,
                created_at=random_date,
                updated_at=random_date,
            )
            
            # Set published_at for published posts
            if status == PostStatus.PUBLISHED:
                # Published date should be after created date
                published_date = fake.date_time_between(
                    start_date=random_date,
                    end_date=end_date,
                    tzinfo=timezone.get_current_timezone()
                )
                post.published_at = published_date
                post.save()
            
            created_count += 1
            
            if created_count % 5 == 0:
                self.stdout.write(f'Created {created_count} posts...')

        # Print summary
        total_posts = Post.objects.count()
        published_posts = Post.objects.filter(status=PostStatus.PUBLISHED).count()
        draft_posts = Post.objects.filter(status=PostStatus.DRAFT).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nGeneration complete!\n'
                f'Total posts: {total_posts}\n'
                f'Published: {published_posts}\n'
                f'Drafts: {draft_posts}\n'
                f'Authors: {len(authors)}'
            )
        )