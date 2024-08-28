# TAO Toolkit - Launcher

This project contains the source code to the TAO launcher interface. This launcher interface aims at providing a unified command line experience to the Transfer Learning Toolkit package.
The DNN's in TAO may be implemented in TensorFlow, Keras or PyTorch. These frameworks are difficult to maintain in the same docker. In an attempt to abstract the final customers of TAO, to handle tao command abstracts these details away from the user.

- [Working with the launcher](docs/working_with_the_launcher.md)
- [Developer instructions](docs/developer_instructions.md)
- [Quick Start Guide](#quick-start-guide)
  - [Software Requirements](#software-requirements)
  - [Installation instructions](#installation-instructions)
- [License](#license)

## Quick Start Guide <a name="quick_start_guide"></a>

This section covers a quick guide to start working with the launcher.

### Software Requirements <a name="software_requirements"></a>

| Software | Version |
| ---- | ------- |
| python | >= 3.6.9 |
| docker-ce | >19.03.5 |
| docker-API | 1.40 |
| [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/overview.html)| >1.3.0-1 |
| nvidia-container-runtime | 3.4.0-1 |
| nvidia-docker2 | 2.5.0-1 |
| nvidia-driver | >450 |

### Installation instructions <a name="installation_instructions"></a>

1. Install docker-ce by following the official [instructions](https://docs.docker.com/engine/install/).

   Once you have installed docker-ce, please follow the [post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/) to make sure that the docker can be run without sudo.

2. Install nvidia-container-toolkit by following these [installation instructions](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

3. Login to the NGC staging area docker registry using the api key generated from `ngc.nvidia.com`

```sh
docker login nvcr.io
```

4. The TAO Launcher can be installed using the wheel from the [google drive](https://drive.google.com/drive/u/1/folders/1-r-Tq6vgyVnb1YsZppteCu9M-zss0Xcs) 
with the command mentioned below. We highly recommend using [python virtualenv](https://python-guide-cn.readthedocs.io/en/latest/dev/virtualenvs.html) to isolate your python env.

```sh
pip install nvidia_tao.0.0.9.dev0-py3x-none-any.whl
```

  Where x is the minor version of the python installed in your PC.

5. Initialize the launcher using `tao init`.

``` {ignore}
2020-11-25 14:07:54,322 [WARNING] __main__: 

************************************************************************************************************************************************************
A config file wasn't found to initialize a TAO instance. Please run the tao init command to get the config file and configure the DL tasks available in TAO.
************************************************************************************************************************************************************

2020-11-25 14:07:54,325 [INFO] tao.components.instance_handler.utils: Downloading the latest config file.
2020-11-25 14:07:54,459 [INFO] tao.components.instance_handler.utils: Download complete. Validating the file.
```

6. Run the tao tasks using the changed tao cli structure.

```sh
tao <task> <sub-task> <cli-args>
```

For detailed instructions on using the launcher, please navigate to this [page](docs/working_with_the_launcher.md).

## <a name='license'></a>License

This project is licensed under the [Apache 2.0](./LICENSE) License.