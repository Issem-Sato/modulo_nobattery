import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# PRAGRAMMA 2
# Obiettivo: definzione taglia ottimale elettrolizzatore per massimizzazione produzione idrogeno e CF da impianto rinnovabile intermittente, considerando modulazione dell'elettrolizzatore

# IPOTESI
# 1. L'elettrolizzatore modula secondo la curva definita dalla funzione...
# 2. Si considerano le fasi di accensione e spegnimento come istantanee
# 3. La potenza dell'impianto PV è definita a priori
# 4. L'ottimizzazione prevede l'ottimo nell'intersezione delle curve CF (monotona decrescente) e Autoconsumo (monotona crescente fino a circa 70% Pmax)
# 5. Non ci sono batterie
# 6. Si condiera che tutta l'energia prodotta dal PV sia usata dall'elettrolizzatore senza altre utenze e criteri di priorità
# 7. Calcolo impianto PV da PVgis # https://re.jrc.ec.europa.eu/pvg_tools/en/ 

class Analisi:
    def __init__(self, file_csv, p_PV, pci, dP):
        self.file_csv = file_csv
        self.p_PV = p_PV # taglia dell'impianto PV
        self.pci = pci # kWh/kgH2 potere calorifico inferiore
        self.dP = dP # granularità ovvero grado di definizione del ciclo iterativo --> sarebbe da valutare la granulosità in funzione dello stack
        self.E_PV = self.load_data()
        self.e_pv = sum(self.E_PV)
        self.P_elc = np.arange(self.p_PV/self.dP, self.p_PV+1, self.p_PV/self.dP)# Range di valori per P_elc (val min, val max, step) in funzione di p_PV, taglia dell'impianto PV
        self.E_H2=[]
        self.E_im=[]
        self.M_H2=[]
        self.Auto=[] # definisco il vettore autoconsumo le cui componenti saranno e_H2
        self.CF=[] # vettore Capacity Factor
        self.E_H2_best=[]
        self.M_H2_best=[]
        self.E_im_best=[]
        self.OFF=[]
        self.off = 0
        self.flag = 0
        self.k = 0
        self.e_H2_best= 0
        self.m_H2_best= 0
        self.e_im_best= 0
        self.cf_best= 0
        self.auto_best= 0
        self.off_best= 0
        self.K = 0

    def load_data(self):
        with open(self.file_csv, 'r') as file:
            lines = file.readlines()
        # Definire l'intestazione esatta desiderata
        header = "time,P,G(i),H_sun,T2m,WS10m,Int"
        # Trova l'indice della riga di intestazione che corrisponde esattamente
        header_idx = next((i for i, line in enumerate(lines) if line.strip() == header), None)
        if header_idx is None:
            raise ValueError("L'intestazione specificata non è stata trovata nel file.")
        # Inizia a leggere i dati dalla riga successiva all'intestazione
        rows = []
        for line in lines[header_idx + 1:]:
            columns = line.strip().split(',')
            if len(columns) == 7:
                rows.append(columns)
            else:
                break  # Interrompe la lettura se incontra una riga con un numero di colonne differente
        data = pd.DataFrame(rows, columns=header.split(','))
        E_PV = pd.to_numeric(data['P'], errors='coerce').dropna()
        E_PV /= 1000  # Converti da W a kW
        return E_PV
    
    #definisco la funzione che esprime la variazione di efficienza (kWhel per kg H2 prodotto da idrolizzatore) al variare della Potenza di esercizio rispetto al nominale
    @staticmethod
    def eff_elc(x):
        y = (-6.1371 * x**6 + 24.394 * x**5 - 39.663 * x**4 + 33.988 * x**3 - 16.412 * x**2 + 4.2929 * x + 0.1022)
        return y
    
    def run_analysis(self):
        for p_elc in self.P_elc:
            p_elc_min = 0.2 * p_elc # Potenza minima di soglia per entrata in lavoro dell'elettrolizzatore
            E_H2_h = []  # vettore energia autoconsumata per produrre idrogeno
            M_H2_h = []  # vettore massa idrogeno prodotto
            E_im_h = []  # vettore energia immessa in rete
            self.off = 0
            self.flag = 1  # indica l'elettrolizzatore spento nell'ora precente
            for p_pv in self.E_PV:
                if p_pv > p_elc:
                    e_H2 = p_elc  # E_H2 è definita qui la prima volta
                    e_im = p_pv - e_H2
                    m_H2 = e_H2 * 0.565 / self.pci  # il valore deriva dall'efficienza effettiva calcolata da funzione
                    self.flag = 0
                elif p_elc_min <= p_pv <= p_elc:
                    e_H2 = p_pv
                    var = p_pv / p_elc  # var è qui definito come ingresso per il lavoro della funzione
                    eta = self.eff_elc(var)  # chiamo la funzione
                    m_H2 = e_H2 * eta / self.pci
                    e_im = 0
                    self.flag = 0
                else:  # qui l'elettrolizzatore non lavora!!
                    e_H2 = 0
                    m_H2 = 0
                    e_im = p_pv
                    if self.flag == 0:  # l'ora precedente era acceso --> si spegne
                        self.off += 1
                        self.flag = 1
                    else:  # l'ora precedente era spento --> continua a rimanere spento
                        self.flag = 1

                E_H2_h.append(e_H2)  # vettore orario di energia in ingresso all'elettrolizzatore
                M_H2_h.append(m_H2)  # vettore orario
                E_im_h.append(e_im)  # vettore orario
            
            e_H2 = sum(E_H2_h)
            e_im = sum(E_im_h)
            m_H2 = sum(M_H2_h)
            
            self.OFF.append(self.off)  # numero spegnimenti per ogni taglia
            e_TOT = len(self.E_PV) * p_elc
            cf = e_H2 / e_TOT * 100
            autoconsumo = e_H2 / self.e_pv * 100
            
            self.CF.append(cf)
            self.Auto.append(autoconsumo)
            self.E_H2.append(e_H2)
            self.E_im.append(e_im)
            self.M_H2.append(m_H2)

            if self.k > 0 and self.CF[self.k] < self.Auto[self.k] and self.CF[self.k - 1] > self.Auto[self.k - 1]:
                self.E_H2_best = E_H2_h
                self.M_H2_best = M_H2_h
                self.E_im_best = E_im_h
                self.e_H2_best = sum(self.E_H2_best)
                self.m_H2_best = sum(self.M_H2_best)
                self.e_im_best = sum(self.E_im_best)
                self.cf_best = self.CF[self.k]
                self.auto_best = self.Auto[self.k]
                self.off_best = self.off
                self.K = self.k
            
            self.k += 1

    def save_results(self):
        # Check if the best results lists are not empty
        if not self.M_H2_best or not self.E_H2_best or not self.E_im_best:
            print("Best results lists are empty. Ensure run_analysis has been executed correctly.")
            return

        df_m_H2 = pd.DataFrame({
            'Massa di H2 prodotta [kg/h]': self.M_H2_best,
            'Energia per la produzione di idrogeno [kWh]': self.E_H2_best,
            'Energia immessa in rete [kWh]': self.E_im_best,
            'Energia prodotta dall\'impianto PV [kWh]': self.E_PV
        })
        # Salva il DataFrame in un file Excel
        df_m_H2.to_excel('media_oraria_H2.xlsx', index=True)

        
    def print_results(self):
        print("Il miglior valore di Potenza Nominale per massimizzare la produzione di idrogeno è pari a", self.P_elc[self.K], "kW")
        print(f"L'energia prodotta dall'impianto PV è pari a {self.e_pv / 1000:.1f} MWh")
        print(f"L'energia autoconsumata per la produzione di idrogeno è pari a {self.e_H2_best / 1000:.1f} MWh")
        print(f"L'energia immessa in rete è pari a {self.e_im_best / 1000:.1f} MWh")
        print(f"L'idrogeno prodotto è pari a {self.m_H2_best:.0f} kg")
        print(f"La % di autoconsumo è pari a {self.auto_best:.1f} %")
        print(f"Il Capacity Factor è pari a {self.cf_best:.1f} %")
        print(f"Il Numero di spegnimenti è pari a", self.off_best)

    def plot_results(self):
        # stampa la massa di idrogeno prodotta
        plt.plot(self.M_H2_best, label="mH2 prodotta [kg/h]")
        plt.xlabel('Ora')
        plt.ylabel('Massa di H2 prodotta [kg]')
        plt.legend()
        plt.show()

        # stampa CF e Autoconsumo
        plt.plot(self.CF, label="Capacity Factor")
        plt.plot(self.Auto, label="Autoconsumo")
        plt.xlabel('Iterazione [#]')
        plt.ylabel('%')
        plt.legend()
        plt.show()

        # stampa le curve di energia
        plt.plot(self.E_H2_best, label="Energia autoconsumata per la produzione di idrogeno")
        plt.plot(self.E_im_best, label="Energia immessa in rete")
        plt.plot(self.E_PV, label="Energia prodotta dall'impianto PV")
        plt.xlabel('Ora')
        plt.ylabel('Energia [kWh]')
        plt.legend()
        plt.show()

        # stampa gli spegnimenti
        plt.plot(self.OFF, label="Numero di spegnimenti")
        plt.xlabel('Potenza elettrolizzatore [kW]')
        plt.ylabel('Spegnimenti [#]')
        plt.legend()
        plt.show()
