Module 1: Personal Website

SSH url: git@github.com:HKipouros/jhu_software_concepts.git

run.py - In this project, I created a personal website that can be launched by running the program run.py. The run.py program begins by importing the third-party Flask module and the “pages” module. The program then instantiates a Flask object called “app” and registers a blueprint based on “pages”. Finally, the program runs “app” within a dunder main block.

pages.py - This program begins by importing Blueprint and render_template from Flask, and then creates a Blueprint instance called “pages”. The program proceeds to define routes for a homepage, contact page, and projects page for the website. Each route includes a function that returns information derived from a respective HTML template using render_template.

templates folder - This folder contains a “base” template containing basic HTML code common to each page, and “home”, “contact”, and “project” that derive from the base. This folder also contains “_navigation” which defines a navigation bar and is included in the base template. I consulted <https://www.w3schools.com/css/css_navbar_horizontal.asp> for an overview of HTML code for a horizontal navigation bar and adapted it to meet my requirements.

static folder - This folder contains a photo which is referenced in the “home” page template and a file called “style.css” that includes CSS styling to personalize the text style and colors used in the HTML templates.