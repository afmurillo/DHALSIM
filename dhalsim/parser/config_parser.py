import logging
import os
import sys
import yaml

from dhalsim.parser.plc_config import PlcConfig

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base class for exceptions in this module."""


class EmptyConfigError(Error):
    """Raised when the configuration file is empty"""


class MissingValueError(Error):
    """Raised when there is a value missing in a configuration file"""


class ConfigParser:
    """
    Class handling the parsing of the input config data.

    :param config_path: The path to the config file of the experiment in yaml format
    :type config_path: str
    """
    def __init__(self, config_path):
        """Constructor method
        """
        self.config_path = os.path.abspath(config_path)

        logger.debug("config file: %s", config_path)
        #Load yaml data from config file
        with open(config_path) as file:
            self.config_data = yaml.load(file, Loader=yaml.FullLoader)
        #Assert config data is not empty
        if not self.config_data:
            raise EmptyConfigError

    @property
    def inp_path(self):
        """Property for the path to the inp file

        :return: absolute path to the inp file
        :rtype: str
        """
        path = self.config_data.get("inp_file")
        if not path:
            raise MissingValueError("inp_file not in config file")
        path = os.path.join(os.path.dirname(self.config_path), path)
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(path+" is not a file")
        return path

    @property
    def cpa_path(self):
        """Property for the path to the cpa file

        :return: absolute path to the cpa file
        :rtype: str
        """
        path = self.config_data.get("cpa_file")
        if not path:
            raise MissingValueError("cpa_file not in config file")
        path = os.path.join(os.path.dirname(self.config_path), path)
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(path + " is not a file")
        return path

    @property
    def cpa_data(self):
        """Property to load the yaml data from the cpa file

        :return: data from cpa file
        """
        with open(self.cpa_path) as file:
            return yaml.load(file, Loader=yaml.FullLoader)

    def generate_plc_configs(self):
        """Returns a list of plc configs

        :return: list containing parsed PlcConfig objects
        :rtype: List[PlcConfig]
        """
        plcs = self.cpa_data.get("plcs")

        plc_config_list = []

        if plcs:
            for plc in plcs:
                name = plc.get("name")
                if not name:
                    raise MissingValueError("plc is missing a name")

                sensor_list = []
                sensors = plc.get("sensors")
                if sensors:
                    for sensor in sensors:
                        sensor_list.append(sensor)

                actuator_list = []
                actuators = plc.get("actuators")
                if actuators:
                    for actuator in actuators:
                        actuator_list.append(actuator)

                plc_config_list.append(PlcConfig(name, sensor_list, actuator_list))

        return plc_config_list



if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    parser = ConfigParser(sys.argv[1])
    parser.generate_plc_configs()
