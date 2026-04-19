from __future__ import annotations

from ukhpi.plotting.theme import go, px  # noqa: F401 — re-exported for ukhpi.plotting.hpi_plots


class PostProcess:
    @staticmethod
    def make_number_readable(num: int | float) -> str:
        """Shorten a number using K/M/B/T suffixes."""
        abs_num = abs(num)
        sign = -1 if num < 0 else 1
        if abs_num < 1000:
            return str(num)

        suffixes = ["", "K", "M", "B", "T"]
        suffix_idx = 0
        while abs_num >= 1000 and suffix_idx < len(suffixes) - 1:
            abs_num /= 1000
            suffix_idx += 1

        formatted = f"{sign * abs_num:.2f}".rstrip("0").rstrip(".")
        return f"{formatted}{suffixes[suffix_idx]}"


class BasicPlots:
    def __init__(self):
        self.df = None
        self.plot_height = 700
        self.plot_width = 1000
        self.autosize = True

    def _assert_data_frame_exists(self):
        if self.df is None:
            raise ValueError("Please initialise the class by setting the dataframe as class.df = df")

    def _assert_column_exists(self, column: str):
        if column not in self.df.columns:
            raise KeyError(f"Column named '{column}' does not exist in the dataframe")

    def _update_layout(
        self,
        fig: go.Figure,
        x_hover: bool = False,
        y_hover: bool = False,
        horizontal_legends: bool = True,
        plot_title: str | None = None,
        height: int | None = None,
        width: int | None = None,
    ) -> go.Figure:
        if x_hover:
            mode = "x"
        elif y_hover:
            mode = "y"
        else:
            mode = None

        return fig.update_layout(
            hovermode=mode,
            legend=dict(orientation="h" if horizontal_legends else "v"),
            title=dict(text=f"<b>{plot_title.upper()}</b>" if plot_title else "<b>PLOT TITLE GOES HERE</b>", x=0.5),
            height=height or self.plot_height,
            width=width or self.plot_width,
            autosize=self.autosize,
        )

    def group_and_plot(
        self,
        plot_type: str,
        group_by_var: str,
        group_metric: str,
        y_var: str,
        marker_color: str = "steelblue",
        pie_colors: list | dict | None = None,
        show_labels: bool = False,
    ) -> go.Figure:
        x_var = group_by_var
        self._assert_data_frame_exists()
        for col in [group_by_var, y_var]:
            self._assert_column_exists(col)

        if group_metric == "sum":
            grouped_df = self.df.groupby([group_by_var], as_index=False, observed=False)[y_var].sum()
        elif group_metric == "mean":
            grouped_df = self.df.groupby([group_by_var], as_index=False, observed=False)[y_var].mean()
        else:
            raise ValueError(f"Unsupported group_metric: {group_metric!r}")

        fig = go.Figure()
        if plot_type == "Pie":
            if not pie_colors:
                pie_colors = px.colors.sample_colorscale(px.colors.sequential.Blues, grouped_df[x_var].nunique())

            fig.add_trace(go.Pie(labels=list(grouped_df[x_var]), values=list(grouped_df[y_var])))
            if isinstance(pie_colors, dict):
                fig.update_traces(marker_colors=grouped_df[x_var].map(pie_colors))
            elif isinstance(pie_colors, list):
                fig.update_traces(marker=dict(colors=pie_colors))

            fig.update_traces(
                hovertemplate=f"<b>{x_var} : </b>%{{label}}<br><b>{y_var} : </b>%{{value}}<br><extra></extra>",
                marker=dict(line=dict(color="#000000", width=2)),
            )
            fig.update_layout(legend=dict(title_text=group_by_var.title()))
        else:
            trace_cls = getattr(go, plot_type)
            kwargs = dict(x=list(grouped_df[x_var]), y=list(grouped_df[y_var]), marker_color=marker_color)
            if show_labels:
                kwargs["text"] = grouped_df[y_var].apply(PostProcess.make_number_readable)
            fig.add_trace(trace_cls(**kwargs))
            fig.update_traces(hovertemplate=f"<b>{x_var} : </b>%{{x}}<br><b>{y_var} : </b>%{{y}}<br><extra></extra>")
            fig.update_yaxes(title=y_var.title())
            fig.update_xaxes(title=x_var.title())
            if plot_type == "Scatter":
                fig.update_traces(mode="markers+lines")

        fig.update_layout(
            title=dict(text=f"<b>{x_var.title()} Vs. {group_metric.title()} of {y_var.title()}</b>", x=0.5)
        )
        return self._update_layout(fig)

    def plot_2_dimensional_data(
        self,
        plot_type: str,
        x_var: str,
        y_var: str,
        marker_color: str = "steelblue",
        show_labels: bool = True,
        orientation: str = "v",
    ) -> go.Figure:
        self._assert_data_frame_exists()
        for col in [x_var, y_var]:
            self._assert_column_exists(col)

        df = self.df
        trace_cls = getattr(go, plot_type)
        kwargs: dict = {"name": y_var}
        if orientation == "h":
            kwargs.update(y=list(df[x_var]), x=list(df[y_var]), orientation="h")
        else:
            kwargs.update(x=list(df[x_var]), y=list(df[y_var]))

        if show_labels:
            kwargs["text"] = df[y_var].apply(PostProcess.make_number_readable)
        else:
            kwargs["customdata"] = df[y_var]

        fig = go.Figure()
        fig.add_trace(trace_cls(**kwargs))

        if orientation == "h":
            hover = f"<b>{x_var} : </b>%{{y}}<br><b>{y_var} : </b>%{{x}}<br><extra></extra>"
            fig.update_xaxes(title=y_var.title())
            fig.update_yaxes(title=x_var.title())
        else:
            hover = f"<b>{x_var} : </b>%{{x}}<br><b>{y_var} : </b>%{{y}}<br><extra></extra>"
            fig.update_yaxes(title=y_var.title())
            fig.update_xaxes(title=x_var.title())

        fig.update_traces(hovertemplate=hover, marker_color=marker_color)
        fig.update_layout(title=dict(text=f"<b>{x_var.title()} Vs. {y_var.title()}</b>", x=0.5))
        if plot_type == "Scatter":
            fig.update_traces(mode="markers+lines")
        return self._update_layout(fig)


class CategoryPlots(BasicPlots):
    def plot_by_categories(
        self,
        plot_type: str,
        id_col: str,
        x_var: str,
        y_var: str,
        colors_dict: dict,
        show_labels: bool = False,
    ) -> go.Figure:
        self._assert_data_frame_exists()
        df = self.df
        if df.empty or not all(col in df.columns for col in [id_col, x_var, y_var]):
            raise KeyError("Some columns are not present in the dataframe")

        trace_cls = getattr(go, plot_type)
        fig = go.Figure()
        for cat in df[id_col].unique():
            filtered = df.loc[df[id_col] == cat]
            kwargs = dict(
                x=list(filtered[x_var]),
                y=list(filtered[y_var]),
                name=str(cat),
                meta=str(cat),
            )
            if colors_dict:
                kwargs["marker_color"] = colors_dict.get(cat)
            if show_labels:
                kwargs["text"] = filtered[y_var].apply(PostProcess.make_number_readable)
            else:
                kwargs["customdata"] = filtered[y_var]
            fig.add_trace(trace_cls(**kwargs))

        fig.update_traces(
            hovertemplate=f"<b>%{{meta}}</b><br><b>{x_var} : </b>%{{x}}<br><b>{y_var} : </b>%{{y}}<br><extra></extra>"
        )
        fig.update_yaxes(title=y_var.title())
        fig.update_xaxes(title=x_var.title())
        fig.update_layout(
            title=dict(text=f"<b>{x_var.title()} Vs. {y_var.title()}</b><br><sup>By {id_col.title()}</sup>", x=0.5),
            legend=dict(title_text=id_col.title()),
        )
        if plot_type == "Scatter":
            fig.update_traces(mode="markers+lines")
        return self._update_layout(fig)


cat_plots = CategoryPlots()
