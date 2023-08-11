import skrf as rf
import matplotlib.pyplot as plt

s2p_filename = "omt"

data12 = rf.Network(s2p_filename + "12.s2p")
data13 = rf.Network(s2p_filename + "13.s2p")
data23 = rf.Network(s2p_filename + "23.s2p")

data = rf.n_twoports_2_nport([data12, data13, data13], nports=3)

data.plot_s_db()
plt.show()

filename = 'output.s3p'
data.write_touchstone(filename, write_z0=True)
