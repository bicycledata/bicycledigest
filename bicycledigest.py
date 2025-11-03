import os
import logging
import yaml

import matplotlib.pyplot as plt
import pandas as pd 

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
                    encoding='utf-8', 
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[
                        logging.FileHandler("digest.log"),
                        logging.StreamHandler()     # logging 'info' level to console as well
                        ]
                    )

class BicycleSession:

    def __init__(self, config='config.yml'):

        with open(config, 'r') as file:
            self.config = yaml.safe_load(file)

        self.threshold = -1
        if self.config['OCOT']['OC'] and self.config['OCOT']['OT']:
            self.threshold = self.config['OCOT']['threshold']

        self.button_file = self.config['Sources']['button_file']
        self.lidar_file = self.config['Sources']['lidar_file']

        self.button_df          = self.load_button_file()
        self.df_ot, self.df_oc  = self.decide_otoc()
        self.lidar_df           = self.load_lidar_file()
        self.events = []

    def print_info(self):
        """
        Print summary info about the session.
        """
        print()
        print('-'*20, "SESSION INFO", '-'*20)
        print("button_file:", session.button_file)
        print('-'*10)
        print("threshold:", session.threshold)
        print('-'*10)
        print("dataframe OTs:\n", session.df_ot)
        print('-'*10)
        print("dataframe OCs:\n", session.df_oc)
        print('-'*10+"\n")

    def load_button_file(self):
        """
        Read in button and return a dataframe.
        """

        filename = os.path.basename(self.button_file)
        
        logging.info(f"Loading button CSV file: {filename}")
        
        df = pd.read_csv(self.button_file, on_bad_lines='skip')
        df = df.loc[df['duration']>0.01]
        df = df.assign(time = pd.to_datetime(df['time'])) # convert strin UTC time to pd.DateTime
        df = df.assign(timedelta = pd.to_timedelta(df['duration'], unit='s')) # timedelta = duration as pd.Timedelta
        df = df.assign(press_start = df['time']-df['timedelta'])
        
        return df

    def load_lidar_file(self):
        """
        Read in lidar file and return a dataframe.
        """

        filename = os.path.basename(self.lidar_file)
        
        logging.info(f"Loading lidar CSV file: {filename}")
        
        df = pd.read_csv(self.lidar_file, on_bad_lines='skip')
        df = df.assign(time = pd.to_datetime(df['time'])) # convert strin UTC time to pd.DateTime

        if 'distance [cm]' in df.columns:
            logging.info(f"Removing units from variable names in the header in {filename}.")
            df.rename(columns={'distance [cm]': 'distance'}, inplace=True)

        # get excerpts based on button presses

        for ps in self.df_ot['press_start']:
            excerpt_start = ps-pd.to_timedelta('3s')
            excerpt_end = ps

            excerpt_df = df.loc[(df['time'] > excerpt_start) & (df['time'] < excerpt_end)]

            plt.scatter(range(len(excerpt_df['time'])), excerpt_df['distance'])
            plt.savefig(os.path.join('out', 'test'+str(ps)+'.png'))
            plt.clf()




        return df

    def decide_otoc(self):
        """
        Return dataframes for OT presses and OC presses based on button press lengths.
        """
        
        logging.info(f"Classifying OTs and OCs from button presses.")

        OTs = self.button_df.loc[self.button_df['duration'] > self.threshold]
        OCs = self.button_df.loc[self.button_df['duration'] <= self.threshold]
        
        logging.info(f"Found {len(OTs)} OTs and {len(OCs)} OCs.")

        return OTs, OCs



if __name__ == "__main__":

    session = BicycleSession()
    # session.print_info()
