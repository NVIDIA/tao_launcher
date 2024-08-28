# TAO Toolkit Quick Start Guide

This page provides a quick start guide for installing and running TAO Toolkit.

## Requirements

### Hardware

The following system configuration is recommended to achieve reasonable training performance with TAO Toolkit and supported models provided:

* 32 GB system RAM
* 32 GB of GPU RAM
* 8 core CPU
* 1 NVIDIA GPU
* 100 GB of SSD space

TAO Toolkit is supported on A100, V100 and RTX 30x0 GPUs.

### Software Requirements

| **Software**                     | **Version** |
| :----- | :---- |
| Ubuntu 18.04 LTS                 | 18.04       |
| python                           | >=3.6.9     |
| docker-ce                        | >19.03.5    |
| docker-API                       | 1.40        |
| [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/overview.html) | >1.3.0-1    |
| nvidia-container-runtime         | 3.4.0-1     |
| nvidia-docker2                   | 2.5.0-1     |
| nvidia-driver                    | >465        |
| python-pip                       | >21.06      |
| python-dev                       |             |

## Installing the Pre-requisites

The tao-launcher is strictly a python3 only package, capable of running on python 3.6.9 or 3.7.

1. Install `docker-ce` by following the [official instructions](https://docs.docker.com/engine/install).

   Once you have installed docker-ce, follow the [post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/) to ensure that the
   docker can be run without `sudo`.

2. Install `nvidia-container-toolkit` by following the [install-guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

3. Get an [NGC](https://ngc.nvidia.com) account and API key:

   a. Go to NGC and click the **TAO Toolkit** container in the **Catalog** tab. This
      message is displayed: `Sign in to access the PULL feature of this repository`.
   b. Enter your Email address and click **Next**, or click **Create an Account**.
   c. Choose your organization when prompted for **Organization/Team**.
   d. Click **Sign In**.

4. Log in to the NGC docker registry (`nvcr.io`) using the command
   `docker login nvcr.io` and enter the following credentials:

    ```sh
      a. Username: $oauthtoken
      b. Password: YOUR_NGC_API_KEY
    ```

   where `YOUR_NGC_API_KEY` corresponds to the key you generated from step 3.

*DeepStream 6.0 - [NVIDIA SDK for IVA inference](https://developer.nvidia.com/deepstream-sdk) is recommended.*

## Installing TAO Toolkit

TAO Toolkit is a Python pip package that is hosted on the NVIDIA PyIndex.
The package uses the docker restAPI under the hood to interact with the NGC Docker registry to
pull and instantiate the underlying docker containers. You must have an NGC account and an API
key associated with your account. See the  [Installation Prerequisites](#installing-the-pre-requisites) section
for details on creating an NGC account and obtaining an API key.

1. Create a new `virtualenv` using `virtualenvwrapper`.

   You may follow the instructions in this [link](https://python-guide-cn.readthedocs.io/en/latest/dev/virtualenvs.html)
   to set up a Python virtualenv using a virtualenvwrapper.

   Once you have followed the instructions to install `virtualenv` and `virtualenvwrapper`,
   set the Python version in the `virtualenv`. This can be done in either of the following ways:
   
      * Defining the environment variable called VIRTUALENVWRAPPER_PYTHON.
        This variable should point to the path where the python3 binary is installed in your local
        machine. You can also add it to your `.bashrc` or `.bash_profile` for setting
        your Python `virtualenv` by default.

         ```sh
         export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
         ```

      * Setting the path to the python3 binary when creating your `virtualenv` using the
        `virtualenvwrapper` wrapper
         
         ```sh
         mkvirtualenv launcher -p /path/to/your/python3
         ```

   Once you have logged into the `virtualenv`, the command prompt should show the name of
   your virtual environment

      ```sh
      (launcher) py-3.6.9 desktop:
      ```

   When you are done with you session, you may deactivate your `virtualenv` using the
   `deactivate` command:

      ```sh
      deactivate
      ```

   You may re-instantiate this created `virtualenv` env using the `workon` command.

      ```sh
      workon launcher
      ```

2. Install the TAO Launcher Python package called `nvidia-tao`.

      ```sh
      pip3 install nvidia-tao
      ```

      >
      >If you had installed an older version of :code:`nvidia-tao` launcher, you may upgrade
      >to the latest version by running the following command.
      >
      >   ```sh
      >   pip3 install --upgrade nvidia-tao
      >   ```

3. Invoke the entrypoints using the :code:`tao` command.

   ```sh
   tao --help
   ```
   
   The sample output of the above command is:
   
   ```sh
   usage: tao [-h]
            {list,stop,info,augment,bpnet,classification,detectnet_v2,dssd,emotionnet,faster_rcnn,fpenet,gazenet,gesturenet,
            heartratenet,intent_slot_classification,lprnet,mask_rcnn,punctuation_and_capitalization,question_answering,
            retinanet,speech_to_text,ssd,text_classification,converter,token_classification,unet,yolo_v3,yolo_v4,yolo_v4_tiny}
            ...

   Launcher for TAO

   optional arguments:
   -h, --help            show this help message and exit

   tasks:
         {list,stop,info,augment,bpnet,classification,detectnet_v2,dssd,emotionnet,faster_rcnn,fpenet,gazenet,gesturenet,heartratenet
        ,intent_slot_classification,lprnet,mask_rcnn,punctuation_and_capitalization,question_answering,retinanet,speech_to_text,
        ssd,text_classification,converter,token_classification,unet,yolo_v3,yolo_v4,yolo_v4_tiny}  
   ```

   Note that under tasks you can see all the launcher-invokable tasks. The following are the
   specific tasks that help with handling the launched commands using the TAO Launcher:

   * list
   * stop
   * info

   >
   > When installing the TAO Toolkit Launcher to your host machine's native python3 as opposed to the recommended route of using virtual 
   > environment, you may get an error saying that `tao` binary wasn't found. This is because the path to your `tao` binary
   > installed by pip wasn't added to the `PATH` environment variable in your local machine. In this case, please run the
   > following command:
   >
   >```sh
   >export PATH=$PATH:~/.local/bin
   >```

## Running the TAO Toolkit

Information about the TAO Launcher CLI and details on using it to run TAO supported tasks are
captured in the [TAO Toolkit Launcher](https://docs.nvidia.com/tao/tao-toolkit/text/tao_launcher.html#tao-toolkit-launcher)
section of the [TAO Toolkit User Guide](https://docs.nvidia.com/tao/tao-toolkit).
