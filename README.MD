# Jenkins On Kubernetes

This project uses [python](https://www.python.org/) and [pulumi](https://www.pulumi.com/), an Infrastructuse as Code (IaC) platfrom to provision Jenkins in [Kubernetes](https://kubernetes.io).

## Getting Started

To manually setup, simply set up your virtual environment: 

`python -m venv venv`

Activate your virtual environment:

`source venv/bin/activate`

Then install the required dependancies:

`pip install -r requirements.txt`

To view changes to be made:

`pulumi preview`

To create your infrastructure:

`pulumi up`

To destroy created infrastructure:

`pulumi destroy`

