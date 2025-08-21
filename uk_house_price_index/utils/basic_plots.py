from .plotly_imports import *
from collections import Counter
from wordcloud import WordCloud
from typing import List, Dict

class PostProcess:

    def make_number_readable(num:(int|float))->str:
        """
        Convert a number to a shortened format with K, M, B, T suffixes.
        
        Examples:
        1000 -> 1K
        1500 -> 1.5K
        1000000 -> 1M
        22364523 -> 22.36M
        
        Args:
            num (int/float): The number to format
            
        Returns:
            str: Formatted number with appropriate suffix
        """
        abs_num = abs(num)
        sign = -1 if num < 0 else 1
        
        if abs_num < 1000:
            return str(num)
        
        suffixes = ['', 'K', 'M', 'B', 'T']
        suffix_idx = 0
        
        while abs_num >= 1000 and suffix_idx < len(suffixes) - 1:
            abs_num /= 1000
            suffix_idx += 1
        
        # Format with 2 decimal places and remove trailing zeros
        formatted = f"{sign * abs_num:.2f}".rstrip('0').rstrip('.') if '.' in f"{sign * abs_num:.2f}" else f"{sign * abs_num:.0f}"
        
        return f"{formatted}{suffixes[suffix_idx]}"

    def make_percent_readable(percent:float)->str:
        return f"{percent:,.2f}%" if not any(noneFmt in str(percent) for noneFmt in ["nan", "NaN", "None"]) else None
        
    def add_source_to_plot(fig:go.Figure, url:str, text:str, x:float=0.95,y:float=-0.2) -> go.Figure:
        """Adds a clickable source annotation to a Plotly figure.

        Adds a hyperlink annotation to the bottom-right corner of the provided Plotly figure, linking to the specified URL and displaying the given text as the source.

        Args:
        fig (go.Figure): The Plotly figure to add the annotation to.
        url (str): The URL to link to.
        text (str): The text to display as the source (e.g., "Data from website X").
        x (float) : x postition (defaults to 0.95)
        y (float) : y position (defaults to -0.2)

        Returns:
            go.Figure: The modified Plotly figure with the added annotation.
        """
        
        fig.add_annotation(
            text = f"""<a href = "{url}" target = "_blank">Source: {text}""",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=x,
            y=y
        )
        return fig

class BasicPlots:
    """
    A class for creating basic data visualizations.

    This class provides a foundation for generating various plots using a pandas DataFrame.  
    It initializes with an empty DataFrame, allowing you to set the data later.

    Attributes:
        df (pandas.DataFrame, optional): The DataFrame to be used for plotting. Defaults to None.
    """
    def __init__(self):
        self.df=None
        self.plot_height = 700
        self.plot_width = 1000
        self.autosize = True

    @property
    def _assert_data_frame_exists(self):
        if self.df is None:
            raise ValueError("Please initialise the class by setting the dataframe as class.df = df")

    def _update_layout(self, 
                      fig:go.Figure, 
                      x_hover:bool=False, 
                      y_hover:bool=False,
                      horizontal_legends:bool=True,
                      plot_title:str=None,
                      height:int=None,
                      width:int=None)->go.Figure:
        if x_hover:
            y_hover = False
            mode = "x"
        elif y_hover:
            x_hover = False
            mode = "y"
        else:
            mode = None

        fig = fig.update_layout(
            hovermode = mode,
            legend = dict(
                orientation = "h" if horizontal_legends else "v"
            ),
            title = dict(
                text = f"<b>{plot_title.upper()}</b>" if plot_title else "<b>PLOT TITLE GOES HERE</b>",
                x = 0.5
            ),
            height = height if height else self.plot_height,
            width = width if width else self.plot_width,
            autosize = self.autosize,
            #barnorm="percent",
          #  barmode="stack"
        )

        return fig
    
    def _adjust_text_formatting(self, 
                              fig:go.Figure,
                              text_template:str = "%{y}",
                              text_position:str = "inside",
                              text_color:str = "black",
                              text_size:int=18,

                              )->go.Figure:
        
        for trace in fig.data:
            if trace.type == "bar":
                if "text_template" in trace:

                    trace.text_template = text_template
                elif "texttemplate" in trace:
                    trace.texttemplate = text_template
                
                trace.textfont = dict(
                                        weight = "bold",
                                        family = "sans serif",
                                        color = text_color
                                    )
                trace.text_position = text_position
                
        #fig = fig.update_traces(
        #    text_template = text_template,
        #    textfont = dict(
        #        weight = "bold",
        #        family = "sans serif",
        #        color = text_color
        #    ),
        #    text_position = text_position
        #)

        fig.update_layout(
            uniformtext = dict(
                minsize = text_size,
                mode = "hide"
            )
        )

        return fig
    
      

    def plot_null_and_non_null_counts(self, show_as_percentage:bool=False) -> go.Figure:
        """Generates a bar chart visualizing the counts or percentages of null and non-null values for each column in a Pandas DataFrame.

        Args:
            show_as_percentage: A boolean flag. If True, the chart displays percentages instead of raw counts. Defaults to False.

        Returns:
            A plotly.graph_objects.Figure object representing the bar chart.  The chart shows stacked bars for each column, one representing null values and the other representing non-null values.  If show_as_percentage is True, the bars represent the percentage of null and non-null values.  Hovering over a bar displays the column name and the count or percentage.

        """

        self._assert_data_frame_exists

        fig = go.Figure()
        
        for col in self.df.columns:
            array = list(self.df[col])
            na, nonNa = array.isna().sum(), array.notna().sum()
            fig.add_trace(
                go.Bar(
                    x=[col],
                    y=[na],
                    name="Null",
                    meta="Null",
                    marker_color="Aquamarine",
                    showlegend=False
                )
            )
            
            fig.add_trace(
                go.Bar(
                    x=[col],
                    y=[nonNa],
                    name="Non-null",
                    meta="Non-null",
                    marker_color="LightSeaGreen",
                    showlegend=False
                )
            )
        
        fig.update_layout(
            barmode="stack",
            #barnorm="percent",
            
        )

        fig = self._update_layout(fig=fig)
        fig.update_xaxes(title="Columns")
        
        if show_as_percentage:
            fig.update_layout(barnorm="percent",
                            title=dict(text="Percentage of null and non-null values by column",
                                        x=0.5))
            fig.update_yaxes(title="Percentage")
            fig.update_traces(
                hovertemplate="<b>Column : </b>%{x}<br>"+
            "<b>%{meta} : </b>%{y:.2f}%<br>" +
            "<extra></extra>"
            )
        else:
            fig.update_layout(
                title=dict(text="Count of null and non-null values by column",
                    x=0.5)
            )
            fig.update_yaxes(title="Count")
            fig.update_traces(
            hovertemplate="<b>Column : </b>%{x}<br>"+
            "<b>%{meta} : </b>%{y}<br>" +
            "<extra></extra>"
        )
        return fig
    
    def _assert_column_exists(self, column:str):
        if not column in self.df.columns:
            raise KeyError(f"Column named '{column}' does not exist in the dataframe")
        else:
            pass

    def plot_histogram_of_column(self, column:str, show_labels:bool=False, orientation:str="v") -> go.Figure:
        """Generates and returns a Plotly histogram of a specified column in the DataFrame.

        Args:
            column (str): The name of the column to generate the histogram for.

        Returns:
            plotly.graph_objects.Figure: A Plotly figure object representing the histogram.  Returns None if the column does not exist.

        Raises:
            AssertionError: If the specified column does not exist in the DataFrame.
        """
        self._assert_data_frame_exists
        self._assert_column_exists(column)
        fig = go.Figure()
        #counts = self.df[column].value_counts().reset_index()
        
        fig.add_trace(
            go.Histogram(
                x=list(self.df[column]),
                orientation="v",
                marker_color="steelblue",
                name = "count",

                #text=grouped_df[y_var].apply(lambda x: PostProcess.make_number_readable(x))
            )
         #go.Bar(
         #    x = counts[column],
         #    y = counts["count"],
         #    marker_color="steelblue",
          #   text = counts["count"].apply(lambda x: PostProcess.make_number_readable(x)) if show_labels else None
         #)
        )
        if show_labels:
            fig.update_traces(
                text_template="%{y:,}", 
                textfont_size=20
            )
        
        fig.update_layout(
            #bargap=0.1,
            title=dict(
                text=f"<b>Histogram of {column}</b>",
                x=0.5
            ),
            
        )

        fig.update_yaxes(title="Count")
        fig = self._update_layout(fig=fig)
        return fig
    
    def plot_histogram_of_data_frame(self):
        """Generates and displays a grid of histograms for each column in a Pandas DataFrame.

        This method asserts that a DataFrame exists within the object (using a private 
        `_assert_data_frame_exists` method), then iterates through each column to create 
        a histogram.  The histograms are arranged in a grid using Plotly's `make_subplots` 
        function for optimal visualization.

        Returns:
            plotly.graph_objects.Figure: A Plotly figure object containing the grid of 
                                        histograms.  Returns None if no DataFrame exists.

        Raises:
            AssertionError: If no DataFrame is found within the object.  (This error is 
                            handled internally via the `_assert_data_frame_exists` method.)
        """
        self._assert_data_frame_exists
        array = self.df.columns

        subplot_specs = SubplotSpecs(array)

        n_rows,n_cols = subplot_specs.get_n_rows_columns()
        specs = subplot_specs.get_subplot_specs(d={})
        rows, cols = subplot_specs.get_subplot_matrices()
        titles = array

        bar_colors = px.colors.sample_colorscale(
            px.colors.sequential.Burgyl,
            len(array)
        )
        fig = make_subplots(rows=n_rows,
                        cols=n_cols,
                        subplot_titles=titles,
                        specs=specs,
                        #vertical_spacing=(1 / (n_rows - 1)),
                        vertical_spacing=0.07
                        )

        for a, column in enumerate(array):
            hist_fig = self.plot_histogram_of_column(column)
            hist_fig.update_traces(marker_color=bar_colors[a])
            
            data=hist_fig.data[0]
            fig.add_trace(data,
                        row=rows[a+1], col=cols[a+1])
        fig.update_layout(
            height=1000,
            title=dict(
                text="<b>Histogram of Columns<b>",
                x=0.5
            )
        )

        fig.update_xaxes(
            tickangle=45,
            nticks=12
        )

        fig.update_yaxes(
            nticks=2
        )

        fig.update_traces(
            showlegend=False,
            hovertemplate="<b>%{x} : </b>%{y}<extra></extra>"
        )
        fig = self._update_layout(fig=fig)
        return fig
    
    def group_and_plot(self,
                     plot_type:str,
                     group_by_var:str,
                     group_metric:str,
                     y_var:str,
                     marker_color:str="steelblue",
                     pie_colors:list|dict=None,
                     show_labels:bool=False) -> go.Figure:
        """Generates and returns a Plotly figure based on grouped data.

        This method groups a DataFrame by a specified variable, calculates a summary statistic 
        (sum or mean), and then generates either a pie chart or other supported Plotly chart types.

        Args:
            plot_type (str): The type of plot to generate. Currently supports "Pie" and other Plotly chart types (e.g., "Scatter", "Bar").
            group_by_var (str): The name of the column to group the DataFrame by.
            group_metric (str): The aggregation function to apply to the grouped data.  Currently supports "sum" and "mean".
            y_var (str): The name of the column to use for the y-axis (or values in a pie chart).
            marker_color (str, optional): The color of the markers in the plot (if applicable). Defaults to "steelblue".
            pie_colors (list|dict, optional):  Colors for the pie chart slices.  Can be a list of colors or a dictionary mapping group_by_var values to colors. Defaults to None.
            show_labels(bool, optional) : Show labels. Defaults to False
        Returns:
            go.Figure: A Plotly figure object representing the generated plot.

        Raises:
            AssertionError: If the DataFrame doesn't exist or if any specified column is missing.
        """
        x_var = group_by_var
        self._assert_data_frame_exists
        for col in [group_by_var, x_var, y_var]:
            self._assert_column_exists(col)
        
        if group_metric == "sum":
            grouped_df = self.df.groupby([group_by_var],
                                        as_index=False,
                                        observed=False)\
                                        [y_var].sum()
            
        elif group_metric == "mean":
            grouped_df = self.df.groupby([group_by_var],
                                        as_index=False,
                                        observed=False)\
                                        [y_var].mean()
        #elif group_metric == "count":
         #   grouped_df = self.df.groupby([group_by_var],
          #                              as_index=False,
           #                             observed=False)\
            #                            [y_var].value_counts()
        
        fig = go.Figure()
        if plot_type == "Pie":
            if not pie_colors:
                pie_colors = px.colors.sample_colorscale(
                    px.colors.sequential.Blues,
                    grouped_df[x_var].nunique()
                )

            fig.add_trace(
                go.Pie(
                    labels=list(grouped_df[x_var]),
                    values=list(grouped_df[y_var]),
                
                )
            )
            if isinstance(pie_colors,dict):
                fig.update_traces(
                    marker_colors=grouped_df[x_var].map(pie_colors)
                )
            elif isinstance(pie_colors, list):
                fig.update_traces(
                    marker=dict(colors=pie_colors)
                )

            fig.update_traces(
                hovertemplate=f"<b>{x_var} : </b>"+ "%{label}<br>" + \
            f"<b>{y_var} : </b>" + "%{value}<br>" +
            "<extra></extra>",
            marker=dict(line=dict(color="#000000",
                                  width=2))
            )

            fig.update_layout(
                legend=dict(
                title_text=group_by_var.title()
            )
            )


        
        else:
            if show_labels:
                    fig.add_trace(
                    eval(f"go.{plot_type}")(
                        x=list(grouped_df[x_var]),
                        y=list(grouped_df[y_var]),
                        marker_color=marker_color,
                        text=grouped_df[y_var].apply(lambda x: PostProcess.make_number_readable(x))
                    )
                )
            else:

                fig.add_trace(
                    eval(f"go.{plot_type}")(
                        x=list(grouped_df[x_var]),
                        y=list(grouped_df[y_var]),
                        marker_color=marker_color
                    )
                )
            fig.update_traces(
                hovertemplate=f"<b>{x_var} : </b>"+ "%{x}<br>" + \
            f"<b>{y_var} : </b>" + "%{y}<br>" +
            "<extra></extra>"
            )


            fig.update_yaxes(title=y_var.title())
            fig.update_xaxes(title=x_var.title())
            
            if plot_type == "Scatter":
                fig.update_traces(
                    mode="markers+lines"
                )

        fig.update_layout(
            title=dict(
                text=f"<b>{x_var.title()} Vs. {group_metric.title()} of {y_var.title()}</b>",
                x=0.5
            ),
        )
        fig = self._update_layout(fig=fig)
        return fig
    
    def plot_2_dimensional_data(self,
                             plot_type:str,
                             x_var:str,
                             y_var:str,
                             marker_color:str="steelblue",
                             show_labels:bool=True,
                             orientation="v"):
        fig = go.Figure()
        self._assert_data_frame_exists
        for col in [x_var, y_var]:
            self._assert_column_exists(col)
        
        df = self.df

        if show_labels:
                if orientation=="h":
                    trace = eval(f"go.{plot_type}")(
                    y=list(df[x_var]),
                    x=list(df[y_var]),
                    orientation = "h",
                    text=df[y_var].apply(lambda x: PostProcess.make_number_readable(x)),
                    name=y_var,
                
            )
                else:
                    trace = eval(f"go.{plot_type}")(
                    x=list(df[x_var]),
                    y=list(df[y_var]),
                    text=df[y_var].apply(lambda x: PostProcess.make_number_readable(x)),
                    name=y_var,
                )
            
                    
                fig.add_trace(trace)
                
        else:
            if orientation == "h":
                trace = eval(f"go.{plot_type}")(
                    y=list(df[x_var]),
                    x=list(df[y_var]),
                    orientation="h",
                    customdata=df[y_var],
                    name=y_var,
                    
                )
            
            else:
                trace = eval(f"go.{plot_type}")(
                    x=list(df[x_var]),
                    y=list(df[y_var]),
                    customdata=df[y_var],
                    name=y_var,
                    
                )

            fig.add_trace(
                trace                
            )

        if orientation == "h":
            temp = f"<b>{x_var} : </b>" + "%{y}<br>" + \
                f"<b>{y_var} :</b>"+ "%{x}<br>" + \
                    "<extra></extra>"
        else:
            temp = f"<b>{x_var} :</b>"+ "%{x}<br>" + \
        f"<b>{y_var} : </b>" + "%{y}<br>" +\
        "<extra></extra>"
            
    
        
        fig.update_traces(
            hovertemplate=temp,
        marker_color=marker_color
        )

        
        if orientation == "h":
            fig.update_xaxes(title=y_var.title())
            fig.update_yaxes(title=x_var.title())
        
        else:

            fig.update_yaxes(title=y_var.title())
            fig.update_xaxes(title=x_var.title())
        fig.update_layout(
            title=dict(
                text=f"<b>{x_var.title()} Vs. {y_var.title()}</b></sup>",
                x=0.5
            ),
            
        )

        if plot_type == "Scatter":
            fig.update_traces(
                mode="markers+lines"
            )
        fig = self._update_layout(fig=fig)
        return fig
    

        

        

    
class DataTable(BasicPlots):
    """
    
    Renders the internal DataFrame as an interactive HTML table using Plotly.
    
    Args:
        BasicPlots (_type_): _description_
    """
    def render_table(self, table_title:str=None, font_size:int=12):
        """Renders the internal DataFrame as an interactive HTML table using Plotly.

        This method asserts that a DataFrame exists within the object before 
        rendering it as a Plotly table.  The table is styled with alternating row colors 
        for improved readability and has a specified width and height.

        Returns:
            plotly.graph_objects.Figure: A Plotly figure object representing the 
                                        interactive HTML table of the DataFrame.  
                                        Returns None if DataFrame is missing.

        Raises:
            AssertionError: If the internal DataFrame (self.df) does not exist.
        """
        self._assert_data_frame_exists
        df=self.df
        fig = go.Figure()

        rowEvenColor = 'lavender'
        rowOddColor = 'white'


        fig.add_trace(
            go.Table(
                header=dict(
                    values=[f"<b>{col.upper()}</b>" for col in df.columns],
                    fill_color="royalblue",
                    align="left",
                    font=dict(color='black', size=font_size)
                ),
                cells=dict(
                    values=[df[col] for col in df.columns],
                    line_color="black",
                    #fill_color="lavender",
                    #fill_color=[[rowOddColor,rowEvenColor,rowOddColor, rowEvenColor,rowOddColor]*(len(df)+1)],
                    fill_color=[[rowOddColor,rowEvenColor,]*(len(df)+1)],
                    align="left",
                    font=dict(color='black', size=font_size-2)
                )
            )
        )

        n = len(df)            # number of rows in your table
        h = 28 + n * 28        # header + rows


        fig.update_layout(
            height=h,
            margin=dict(l=0, 
                        r=0, 
                        t=0 if not table_title else 60, 
                        b=0),
            title = dict(
                text = f"<b>{table_title.upper()}</b>" if table_title else "<b>TABLE TITLE GOES HERE</b>",
                x = 0.5
            )
        )
        #fig.update_layout(width=900, height=700)
        #self.plot_height, self.plot_width = 300
        #fig = self._update_layout(fig=fig, plot_title=table_title)
        return fig
    
    

    
class CategoryPlots(BasicPlots):


    def bar_plot_by_categories_ordered_by_value(self,
                                          grouped_df:pd.DataFrame,
                                      # stageIGroupByCols:(str|list[str, str]),
                                       y_var:str,
                                       x_var:str,
                                       colors_dict:dict,
                                       id_col:str,
                                       sort_ascending:(bool|list[bool, bool]),
                                       sort_cols:(str|list[str, str])=None,
                                        stage_2_group_by_col:str=None,
                                        orientation:str="v")->go.Figure:
        
        
        #df=self.df
        #self._assert_data_frame_exists

        df = grouped_df.copy()
        groupByCol = stage_2_group_by_col if stage_2_group_by_col else x_var
        sort_cols = sort_cols if sort_cols else [x_var, y_var]
        orderedDict = (
            df
            .sort_values(sort_cols, ascending=sort_ascending)
            .groupby(groupByCol)[id_col]
            .apply(list)
            .to_dict()
        )

        fig = go.Figure()

        

        for key, groups in orderedDict.items():
            for group in groups:
                value = df.loc[
                    (
                        df[id_col]==group
                    )  & 
                    (
                        df[groupByCol]==key
                    ),
                    y_var
                ].iloc[0]
                if orientation == "v":
                    trace = go.Bar(
                        x = [key],
                        y = [value],
                        name = group, 
                        meta = group,
                        legendgroup=group,
                        text_template="%{y}",
                        marker=dict(
                            color = colors_dict.get(group)
                        )
                      #  hovertemplate="<b>"+ +" : </b>%{x}<br><b>Team : </b>%{meta}<br><b>Wins : </b>%{y}<extra></extra>"
                    )
                elif orientation == "h":
                    trace = go.Bar(
                        y = [key],
                        x = [value],
                        name = group, 
                        meta = group,
                        legendgroup=group,
                        orientation = "h",
                        text_template="%{y}",
                        marker=dict(
                            color = colors_dict.get(group)
                        )
                      #  hovertemplate="<b>"+ +" : </b>%{x}<br><b>Team : </b>%{meta}<br><b>Wins : </b>%{y}<extra></extra>"
                    )

                fig.add_trace(
                    trace
        
                )

        seen = set()
        for trace in fig.data:
            if trace.name in seen:
                trace.showlegend = False
            else:
                seen.add(trace.name)
                trace.legendgroup = trace.name

        
        fig = self._adjust_text_formatting(fig)
        return fig
    
    def plot_by_categories(self,
        #df:pd.DataFrame,
        plot_type:str,
        id_col:str,
        x_var:str,
        y_var:str,
        colors_dict:dict,
        show_labels:bool=False
            ) -> go.Figure :
        
        """Generates a Plotly figure showing different categories of data.

        This function creates a Plotly plot (scatter, line, etc.) where data is 
        grouped and visualized based on categories specified in `id_col`.  Each 
        category gets its own trace on the plot with a color determined by 
        `colors_dict`.

        Args:
            plot_type (str): The type of Plotly plot to create (e.g., "Scatter", "Line").  
                             Must be a valid Plotly plot type.
            id_col (str): The name of the column containing category labels.
            x_var (str): The name of the column to use for the x-axis values.
            y_var (str): The name of the column to use for the y-axis values.
            colors_dict (dict): A dictionary mapping category labels (from `id_col`) to colors. 
                               If a category is not found in the dictionary, it defaults to the Plotly default color.

            show_labels(bool, optional) : Show labels. Defaults to False
        Returns:
            go.Figure: A Plotly figure object.  Returns None if the DataFrame is empty or missing required columns.

        Raises:
            KeyError: If any of the specified columns (`id_col`, `x_var`, `y_var`) are not found in the DataFrame.
            Exception: If there is an error during plot generation (e.g., invalid `plot_type`).

        Notes:
            This function assumes that a DataFrame has been previously set using the `self.df` attribute. It internally checks for DataFrame existence and validity.  
        """

        df=self.df
        self._assert_data_frame_exists

        if df is not None:
            if not df.empty:
                if not all(col in df.columns for col in [
                    id_col,
                    x_var,
                    y_var
                ]):
                    raise KeyError("Some columns are not present in the dataframe")
        
        fig = go.Figure()
        
        for cat in df[id_col].unique():
            filteredForCat = df.loc[df[id_col]==cat]
            if colors_dict:
                if show_labels:

                    fig.add_trace(
                        eval(f"go.{plot_type}")(
                            x=list(filteredForCat[x_var]),
                            y=list(filteredForCat[y_var]),
                            name=str(cat),
                            meta=str(cat),
                            text=filteredForCat[y_var].apply(lambda x: PostProcess.make_number_readable(x)),
                            
                            marker_color=colors_dict.get(cat)
                        )
                    )
                else:
                    fig.add_trace(
                        eval(f"go.{plot_type}")(
                            x=list(filteredForCat[x_var]),
                            y=list(filteredForCat[y_var]),
                            name=str(cat),
                            meta=str(cat),
                            #text=filteredForCat[y_var],
                            marker_color=colors_dict.get(cat)
                        )
                    )
            else:
                if show_labels:
                        fig.add_trace(
                        eval(f"go.{plot_type}")(
                            x=list(filteredForCat[x_var]),
                            y=list(filteredForCat[y_var]),
                            text=filteredForCat[y_var].apply(lambda x: PostProcess.make_number_readable(x)),
                            name=str(cat),
                            meta=str(cat),
                        )
                    )
                else:

                    fig.add_trace(
                        eval(f"go.{plot_type}")(
                            x=list(filteredForCat[x_var]),
                            y=list(filteredForCat[y_var]),
                            customdata=filteredForCat[y_var],
                            name=str(cat),
                            meta=str(cat),
                        )
                    )

        
        
        fig.update_traces(
            hovertemplate="<b>%{meta}</b><br>" + \
        f"<b>{x_var} :</b>"+ "%{x}<br>" + \
        f"<b>{y_var} : </b>" + "%{y}<br>" +
        "<extra></extra>"
        )

        

        fig.update_yaxes(title=y_var.title())
        fig.update_xaxes(title=x_var.title())
        fig.update_layout(
            title=dict(
                text=f"<b>{x_var.title()} Vs. {y_var.title()}</b><br><sup>By {id_col.title()}</sup>",
                x=0.5
            ),
            legend=dict(
                title_text=id_col.title()
            )
        )

        if plot_type == "Scatter":
            fig.update_traces(
                mode="markers+lines"
            )

        fig = self._update_layout(fig=fig)
        return fig

class WordCloudGenerator:
    def __init__(self):
        pass

    @classmethod
    def calculate_word_counters(cls, words_list:List[str])->Dict[str, int]:
        counters_found = Counter(words_list)
        counts_dict = dict(counters_found.items())
        return dict(sorted(counts_dict.items(), key = lambda x: x[1], reverse=True))
    
    @classmethod
    def generate_word_cloud(cls, words_list:List[str], word_counter:Dict[str, int]=None)->go.Figure:
        word_counter = cls.calculate_word_counters(words_list=words_list)
        word_cloud=WordCloud(background_color='black', 
                            width=2160, 
                            height=600,
                            colormap="Blues"
                        )
        fig = px.imshow(word_cloud.fit_words(word_counter).to_image())
        
        fig.update_layout(
                        xaxis={'visible': False},
                        yaxis={'visible': False},
                        margin={"t":0, 'b': 0, 'l': 0, 'r': 0},
                        hovermode=False,
                        paper_bgcolor="black",
                        plot_bgcolor="black",
        
        
                )
        return fig 

    

    
    
