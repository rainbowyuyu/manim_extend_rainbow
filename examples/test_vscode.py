from manim import *

class TestVSCode(Scene):
    def construct(self):

        axes = Axes( 
            x_range=[-8, 9, 2], 
            y_range=[-6, 7, 2], 
            x_length=4, 
            y_length=4, 
            axis_config={'include_numbers': True, 'numbers_to_exclude': [0]}, 
            x_axis_config={'color': ORANGE}, 
            y_axis_config={'color': ORANGE}, 
        ) 
        axes_label = axes.get_axis_labels(x_label='x', y_label='f(x)') 
        graph = axes.plot(lambda x: 5*np.e ** (-x**2/2), x_range=[-5, 5], color=YELLOW) 
        graph_label = axes.get_graph_label(graph, label='e^{-x^2}', color=YELLOW, x_val=1,dot=False)
        vgp = VGroup()
        vgp.add(axes, graph, graph_label, axes_label)
        self.play(Create(vgp))
        self.wait()