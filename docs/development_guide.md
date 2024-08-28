# Developer Guide
The contents on this page should give information about development guidelines
and the steps required to get started with contributing to the development of
Ansible-automated Data Collection (ADC).
---
## ADC Development or Test Environment setup

For SERO Linux Terminal Servers (seroiutsXXXX), there already have existed
python3 virtual ENV (ansible is already installed by `pip`), the python version
is 3.8 and ansible-core version is 2.12.1. The ansible command will be present
when python3 venv is loaded.

Another way is to new a ADC environment with python3 venv, see the following steps:

We assume that you are using `adc_venv` as name for the directory the
virtual environment is in. If you want to, you can use another name; then
replace "adc_venv" with your preferred name in the instructions below.

**For SERO Linux Terminal Server, GIC and other machines with modules:**

1. Load the module containing among other things `python`, `virtualenv` and
`pip`. This is needed on for instance GIC Rosersberg. You might have use for
it in other environments, but if the command does not exist, you can ignore
this step and install Python, `python`, `virtualenv` and `pip` in some other
way.
    ```
    $ module load python/3.8-addons-virtualenv
    ```

2. Create a virtual environment.
    ```
    $ virtualenv adc_venv
    ```

3. Unload the modules to fix a bug that causes `pip` to raise `ImportError`.
    ```
    $ module unload python/3.8-addons-virtualenv
    ```

**Activiate and install required modules after python3.8 virtualenv is created as above step**

1. For `bash` and `zsh`:

   ```
   $ source adc_venv/bin/activate
   ```

2. For `tcsh` or `csh`:

   ```
   $ source adc_venv/bin/activate.csh
   ```

3. Upgrade pip and install required modules
   ```
   $ pip install pip --upgrade
   $ pip install -r requirements.txt
   ```
