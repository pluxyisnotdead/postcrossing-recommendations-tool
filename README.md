# Postcrossing recommendations tool

This repository contains a project developed during a summer internship at Azati. The project explores the use of Gradio for building interactive machine learning recommendations tool, based on images and text profile descriptions.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)

## Introduction

The main goal of this project is to use Selenium to scrape user data from postcrossing.com, including their favorite postcards and profile descriptions. This data is then used to recommend images to users based on the content of their profiles and their favorite images.

## Features

- Scraping user data from postcrossing.com using Selenium
- Extracting and analyzing user profile descriptions and favorite postcards
- Recommending images to users based on their profile data and favorite images
- Interactive UI for displaying recommendations using Gradio
- Integration with popular machine learning libraries like PyTorch and Transformers

## Installation

To get started with this project, clone the repository and install the required dependencies:

```bash
git clone https://github.com/pluxyisnotdead/postcrossing-recommendations-tool.git
cd gradio-tryouts
pip install -r requirements.txt
```

## Usage

After installing the dependencies, you can run the demos provided in the repository.

```bash
python interface.py
```

And then follow the URL in console to use the tool.

## Dependencies

The project relies on the following Python libraries:

- [Gradio](https://github.com/gradio-app/gradio)
- [PyTorch](https://pytorch.org/)
- [Transformers](https://github.com/huggingface/transformers)
- [Pillow](https://python-pillow.org/)
- [SciPy](https://www.scipy.org/)
- [Requests](https://docs.python-requests.org/en/latest/)
- [Selenium](https://www.selenium.dev/)
- [CLIP Model](https://github.com/openai/CLIP)

These dependencies are listed in the `requirements.txt` file and can be installed using `pip`.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

Developed during a summer internship at Azati.
