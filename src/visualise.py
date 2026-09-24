"""Charts and maps. Every function writes a standalone HTML file to output/.

Plotly ships its own world geometry, so the choropleths need no shapefile
download and the HTML files open offline in any browser.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import OUTPUT, COUNTRY_CENTROIDS, INDIAN_PORTS
import analysis as an

# Tradestat country spellings that pycountry / plotly won't match.
NAME_FIXES = {
    # Real DGCI&S spellings taken from the Tradestat country dropdown.
    # Keys are Title Case because _clean_names() applies .str.title() first.
    "Bangladesh Pr": "Bangladesh",
    "China P Rp": "China",
    "Egypt A Rp": "Egypt",
    "Korea Rp": "South Korea",
    "Korea Dp Rp": "North Korea",
    "Vietnam Soc Rep": "Vietnam",
    "Sri Lanka Dsr": "Sri Lanka",
    "Pakistan Ir": "Pakistan",
    "U Arab Emts": "United Arab Emirates",
    "U K": "United Kingdom",
    "U S A": "United States",
    "Saudi Arab": "Saudi Arabia",
    "Netherland": "Netherlands",
    "Tanzania Rep": "Tanzania",
    "Baharain Is": "Bahrain",
    "Bosnia-Hrzgovin": "Bosnia and Herzegovina",
    "Congo D. Rep.": "Democratic Republic of the Congo",
    "Congo P Rep": "Republic of the Congo",
    "Cote D' Ivoire": "Ivory Coast",
    "Dominic Rep": "Dominican Republic",
    "Slovak Rep": "Slovakia",
    "Czech Republic": "Czechia",
    "Macedonia": "North Macedonia",
    "Lao Pd Rp": "Laos",
    "Kyrghyzstan": "Kyrgyzstan",
    "Yemen Republc": "Yemen",
    "Panama Republic": "Panama",
    "Fiji Is": "Fiji",
    "Nauru Rp": "Nauru",
    "Vanuatu Rep": "Vanuatu",
    "Kiribati Rep": "Kiribati",
    "C Afri Rep": "Central African Republic",
    "Equtl Guinea": "Equatorial Guinea",
    "Guinea Bissau": "Guinea-Bissau",
    "Cape Verde Is": "Cape Verde",
    "State Of Palest": "Palestine",
    "Timor Leste": "Timor-Leste",
    "Turkey": "Turkey",
    "Russia": "Russia",
    "Iran": "Iran",
    "Syria": "Syria",
    "Cocos Is": 'Cocos Islands',
    "Christmas Is.": 'Christmas Island',
    "Cayman Is": 'Cayman Islands',
    "Cook Is": 'Cook Islands',
    "Falkland Is": 'Falkland Islands',
    "Faroe Is.": 'Faroe Islands',
    "Fr Guiana": 'French Guiana',
    "Fr Polynesia": 'French Polynesia',
    "Marshall Island": 'Marshall Islands',
    "Papua N Gna": 'Papua New Guinea',
    "Solomon Is": 'Solomon Islands',
    "Norfolk Is": 'Norfolk Island',
    "Pitcairn Is.": 'Pitcairn Islands',
    "St Kitt N A": 'St Kitts and Nevis',
    "Turks C Is": 'Turks and Caicos',
    "Virgin Is Us": 'Virgin Islands',
    "Br Virgn Is": 'British Virgin Islands',
    "Wallis F Is": 'Wallis and Futuna',
    "Ameri Samoa": 'American Samoa',
    "Niue Is": 'Niue',
    "Tokelau Is": 'Tokelau',
    "Sao Tome": 'Sao Tome',
    "Netherlandantil": 'Curacao',
    "Sint Maarten (Dutch Part)": 'Sint Maarten',
    "Swaziland": 'Swaziland',
    "Sahrawi A.Dm Rp": None,
    "Antartica": None,
    "Neutral Zone": None,
    "Pacific Is": None,
    "Panama C Z": None,
    "Channel Is": None,
    "Heard Macdonald": None,
    "British Indian": None,
    "Us Minor Outlying Islands": None,
    "Svallbard And J": None,
    "Installations In International Waters": None,
    "Union Of Serbia & Montenegro": None,
    "Fr S Ant Tr": None,
    # Aggregate rows -- not real destinations, dropped downstream.
    "Unspecified": None,
    "Trade To Unspecified Countries": None,
}


def _clean_names(s: pd.Series) -> pd.Series:
    return s.str.title().str.strip().replace(NAME_FIXES)


def choropleth(df: pd.DataFrame, period: str | None = None,
               filename: str = "map_exports_by_destination.html") -> str:
    """World map of export value by destination, animated across periods."""
    a = an.annual_by_country(df)
    a["country_clean"] = _clean_names(a["country"])
    if period:
        a = a[a["period"] == period]

    fig = px.choropleth(
        a.sort_values("period"),
        locations="country_clean",
        locationmode="country names",
        color="value_usd_mn",
        hover_name="country_clean",
        animation_frame=None if period else "period",
        color_continuous_scale="Blues",
        range_color=(0, a["value_usd_mn"].quantile(0.97)),
        labels={"value_usd_mn": "US$ mn"},
        title="India's yarn exports by destination (US$ million)",
    )
    fig.update_geos(showcoastlines=True, coastlinecolor="#999",
                    showland=True, landcolor="#f4f4f4", projection_type="natural earth")
    fig.update_layout(margin=dict(l=0, r=0, t=60, b=0), height=560)

    path = OUTPUT / filename
    fig.write_html(path, include_plotlyjs="cdn")
    return str(path)


def quadrant(df: pd.DataFrame, min_value: float = 5.0,
             filename: str = "chart_market_quadrant.html") -> str:
    """Size vs growth scatter -- the 'where should we push' chart."""
    q = an.market_quadrant(df, min_value=min_value)
    q["country_clean"] = _clean_names(q["country"])
    size_cut = q["size_threshold"].iloc[0]

    fig = px.scatter(
        q, x="value_last", y="cagr_pct",
        size="total_period", color="quadrant",
        hover_name="country_clean", text="country_clean",
        log_x=True, size_max=45,
        color_discrete_map={"Core": "#1F3864", "Emerging": "#2E9E5B",
                            "Mature": "#C08A2E", "Marginal": "#B0B0B0"},
        labels={"value_last": "Market size, latest period (US$ mn, log scale)",
                "cagr_pct": "CAGR over period (%)"},
        title="Market attractiveness: size vs growth",
    )
    fig.update_traces(textposition="top center",
                      textfont=dict(size=9, color="#444"))
    fig.add_hline(y=0, line_dash="dash", line_color="#888")
    fig.add_vline(x=size_cut, line_dash="dash", line_color="#888")
    fig.update_layout(height=620, margin=dict(l=60, r=20, t=60, b=60))

    path = OUTPUT / filename
    fig.write_html(path, include_plotlyjs="cdn")
    return str(path)


def concentration(df: pd.DataFrame,
                  filename: str = "chart_concentration_risk.html") -> str:
    """HHI trend with the top-1 and top-5 dependence overlaid."""
    h = an.hhi(df)
    fig = go.Figure()
    fig.add_bar(x=h["period"], y=h["hhi"], name="HHI",
                marker_color="#1F3864", yaxis="y")
    fig.add_scatter(x=h["period"], y=h["top5_share_pct"], name="Top 5 share (%)",
                    mode="lines+markers", line=dict(color="#C00000", width=2),
                    yaxis="y2")
    fig.add_scatter(x=h["period"], y=h["top1_share_pct"], name="Top 1 share (%)",
                    mode="lines+markers", line=dict(color="#C08A2E", width=2, dash="dot"),
                    yaxis="y2")
    fig.add_hline(y=2500, line_dash="dash", line_color="#888",
                  annotation_text="Highly concentrated threshold")
    fig.update_layout(
        title="Destination concentration risk over time",
        yaxis=dict(title="HHI (0-10,000)"),
        yaxis2=dict(title="Share of total exports (%)", overlaying="y",
                    side="right", range=[0, 100]),
        height=520, margin=dict(l=60, r=60, t=60, b=60),
        legend=dict(orientation="h", y=-0.18),
    )
    path = OUTPUT / filename
    fig.write_html(path, include_plotlyjs="cdn")
    return str(path)


def seasonality_chart(df: pd.DataFrame,
                      filename: str = "chart_seasonality.html") -> str:
    """Monthly seasonal index. Needs MEIDB monthly data."""
    s = an.seasonality(df)
    fig = px.bar(s, x="month_name", y="seasonal_index",
                 error_y="std_dev",
                 labels={"seasonal_index": "Seasonal index (100 = average month)",
                         "month_name": ""},
                 title="Seasonality of India's yarn exports")
    fig.update_traces(marker_color="#1F3864")
    fig.add_hline(y=100, line_dash="dash", line_color="#C00000")
    fig.update_layout(height=460, margin=dict(l=60, r=20, t=60, b=40))
    path = OUTPUT / filename
    fig.write_html(path, include_plotlyjs="cdn")
    return str(path)


def trade_lanes(df: pd.DataFrame, port: str = "Nhava Sheva (JNPT)",
                top_n: int = 25,
                filename: str = "map_trade_lanes.html") -> str:
    """Great-circle flow map from an Indian port to top destinations.

    Line width scales with export value. Destination coordinates are
    approximate centroids -- indicative geometry, not survey data.
    """
    a = an.annual_by_country(df)
    latest = a[a["period"] == a["period"].max()]
    latest = (latest.groupby("country", as_index=False)["value_usd_mn"].sum()
                    .nlargest(top_n, "value_usd_mn"))
    latest["country_clean"] = _clean_names(latest["country"])

    if port not in INDIAN_PORTS:
        raise KeyError(f"Unknown port. Options: {list(INDIAN_PORTS)}")
    olat, olon = INDIAN_PORTS[port]
    vmax = latest["value_usd_mn"].max()

    fig = go.Figure()
    plotted = 0
    for _, r in latest.iterrows():
        coords = COUNTRY_CENTROIDS.get(r["country_clean"]) \
            or COUNTRY_CENTROIDS.get(r["country"])
        if not coords:
            continue
        dlat, dlon = coords
        fig.add_trace(go.Scattergeo(
            lat=[olat, dlat], lon=[olon, dlon], mode="lines",
            line=dict(width=max(0.8, 7 * r["value_usd_mn"] / vmax),
                      color="#1F3864"),
            opacity=0.55, hoverinfo="text",
            text=f"{port} → {r['country_clean']}: US$ {r['value_usd_mn']:,.1f} mn",
            showlegend=False,
        ))
        fig.add_trace(go.Scattergeo(
            lat=[dlat], lon=[dlon], mode="markers",
            marker=dict(size=6 + 16 * r["value_usd_mn"] / vmax,
                        color="#C00000", opacity=0.75),
            hoverinfo="text", text=f"{r['country_clean']}: US$ {r['value_usd_mn']:,.1f} mn",
            showlegend=False,
        ))
        plotted += 1

    fig.add_trace(go.Scattergeo(
        lat=[olat], lon=[olon], mode="markers+text",
        marker=dict(size=13, color="#1F3864", symbol="square"),
        text=[port], textposition="bottom center", showlegend=False,
    ))
    fig.update_geos(projection_type="natural earth", showland=True,
                    landcolor="#f4f4f4", coastlinecolor="#bbb", showcountries=True,
                    countrycolor="#ddd")
    fig.update_layout(
        title=f"Yarn export lanes from {port} ({plotted} destinations, latest period)",
        height=580, margin=dict(l=0, r=0, t=60, b=0))

    path = OUTPUT / filename
    fig.write_html(path, include_plotlyjs="cdn")
    return str(path)
