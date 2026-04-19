import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import pandas as pd
import numpy as np
import json
from utils import get_market_overview_data, get_auto_tickers_data, get_historical_sector_data, get_sector_news, AESTHETIC_COLORS

def render():
    st.markdown('<h1 class="gradient-text">Global Market Overview</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#8fc1d4;'>Real-time macro analysis and sector intelligence.</p>", unsafe_allow_html=True)

    df_market = get_market_overview_data()
    live_data = get_auto_tickers_data()
    df_market['Pct Change'] = df_market['Company'].map(lambda x: live_data.get(x, (0, 0))[1])
    hist_data = get_historical_sector_data()

    highest_co = df_market.loc[df_market['Market Cap'].idxmax()]
    lowest_co = df_market.loc[df_market['Market Cap'].idxmin()]
    total_mcap = df_market['Market Cap'].sum()

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="kpi-card"><p class="metric-label">Sector Total Market Cap</p><h2 style="margin:0; font-size:2rem; font-weight:800; color:white;">${total_mcap/1e9:.1f} <span style="color:#00C9FF;">Billion</span></h2></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><p class="metric-label">Most Valuable (Leader)</p><h2 style="margin:0; font-size:2rem; font-weight:800; color:white;">{highest_co["Company"]}</h2><p style="margin:0; color:#92FE9D; font-weight:bold;">${highest_co["Market Cap"]/1e9:.1f}B</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><p class="metric-label">Least Valuable (Laggard)</p><h2 style="margin:0; font-size:2rem; font-weight:800; color:white;">{lowest_co["Company"]}</h2><p style="margin:0; color:#ef473a; font-weight:bold;">${lowest_co["Market Cap"]/1e9:.1f}B</p></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    r2_c1, r2_c2 = st.columns([2.5, 1], gap="large")
    with r2_c1:
        st.markdown("<p class='section-title'>SECTOR MARKET SHARE</p>", unsafe_allow_html=True)
        
        # --- THIRD PARTY JAVASCRIPT: PREMIUM GRADIENT PIE CHART ---
        chart_data = []
        for i, (name, val) in enumerate(zip(df_market['Company'], df_market['Market Cap'])):
            base_color = AESTHETIC_COLORS[i % len(AESTHETIC_COLORS)]
            gradient_end = base_color + "66" 
            
            chart_data.append({
                "value": float(val),
                "name": name,
                "itemStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": base_color},
                            {"offset": 1, "color": gradient_end}
                        ]
                    },
                    "shadowColor": base_color
                }
            })
        js_data = json.dumps(chart_data)

        # Inject HTML, CSS, and the JS ECharts library
        echarts_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
        </head>
        <body style="margin:0; padding:0; background:transparent;">
            <div id="chart" style="width: 100%; height: 380px;"></div>
            <script>
                var chartDom = document.getElementById('chart');
                var myChart = echarts.init(chartDom, 'dark');
                var option = {{
                    backgroundColor: 'transparent',
                    tooltip: {{
                        trigger: 'item',
                        backgroundColor: 'rgba(10, 20, 25, 0.95)',
                        borderColor: '#00C9FF',
                        textStyle: {{ color: '#fff', fontFamily: 'Inter' }},
                        formatter: function(params) {{
                            var valBillion = (params.value / 1e9).toFixed(2);
                            return '<b style="font-size:16px;color:' + params.color.colorStops[0].color + '">' + params.name + '</b><br/>' +
                                   'Market Cap: <b>$' + valBillion + 'B</b><br/>' +
                                   'Share: <b>' + params.percent + '%</b><br/><br/>' +
                                   '<span style="font-size:10px; color:#8fc1d4;">Click to view on Yahoo Finance ↗</span>';
                        }}
                    }},
                    series: [{{
                        name: 'Market Share',
                        type: 'pie',
                        radius: ['48%', '75%'],
                        avoidLabelOverlap: false,
                        itemStyle: {{
                            borderRadius: 6,
                            borderWidth: 0
                        }},
                        label: {{ 
                            show: true, 
                            formatter: '{{b}}\\n{{d}}%', 
                            color: '#e0e0e0',
                            fontWeight: '600'
                        }},
                        emphasis: {{
                            scale: true,
                            scaleSize: 6,
                            label: {{ show: true, fontSize: 18, fontWeight: 'bold', color: '#fff' }},
                            itemStyle: {{
                                shadowBlur: 25,      
                                shadowOffsetX: 0,
                                shadowOffsetY: 0
                            }}
                        }},
                        data: {js_data}
                    }}]
                }};
                myChart.setOption(option);

                // Add Click Listener to redirect to Yahoo Finance
                myChart.on('click', function (params) {{
                    var urls = {{
                        'Audi': 'https://finance.yahoo.com/quote/NSU.DE',
                        'BMW': 'https://finance.yahoo.com/quote/BMW.DE',
                        'VW': 'https://finance.yahoo.com/quote/VOW3.DE',
                        'GM': 'https://finance.yahoo.com/quote/GM',
                        'Ford': 'https://finance.yahoo.com/quote/F'
                    }};
                    if (urls[params.name]) {{
                        window.open(urls[params.name], '_blank');
                    }}
                }});
            </script>
        </body>
        </html>
        """
        # Render the JS component seamlessly inside Streamlit
        components.html(echarts_html, height=400)

    with r2_c2:
        html_news = '<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:20px; height:410px; overflow-y:auto;">\n'
        html_news += "<p style='font-weight: 600; letter-spacing: 1px; color: #8fc1d4; font-size: 13px; text-transform: uppercase; margin-bottom: 15px;'>📰 LIVE SECTOR NEWS</p>\n"
        news = get_sector_news()
        if news:
            for item in news:
                date_display = item.get('date_str', 'Recent')
                html_news += f"""<div class="news-box"><a href="{item['link']}" target="_blank" style="color:#00C9FF; text-decoration:none; font-weight:700; font-size:13px; display:block;">🔗 {item['title']}</a><p style="margin:5px 0 0 0; color:#aaa; font-size:11px;">Source: {item['publisher']} • <span style="color:#92FE9D; font-weight:bold;">{date_display}</span></p></div>\n"""
        else:
            html_news += "<p style='color:#aaa; font-size:12px;'>Awaiting latest news updates...</p>\n"
        html_news += "</div>"
        st.markdown(html_news, unsafe_allow_html=True)

    r3_c1, r3_c2 = st.columns([2, 1.5], gap="large")
    with r3_c1:
        st.markdown("<p class='section-title'>NORMALIZED RELATIVE PERFORMANCE (1 YEAR)</p>", unsafe_allow_html=True)
        if not hist_data.empty:
            df_norm = (hist_data / hist_data.iloc[0] - 1) * 100
            fig_perf = px.line(df_norm, color_discrete_sequence=AESTHETIC_COLORS)
            fig_perf.update_layout(template="plotly_dark", paper_bgcolor='rgba(255,255,255,0.03)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, l=10, r=10, b=20), height=350, yaxis_title="Gain/Loss (%)", xaxis_title="", legend_title="", hovermode="x unified")
            fig_perf.update_traces(line=dict(width=2.5))
            st.plotly_chart(fig_perf, use_container_width=True)
        else:
            st.caption("Fetching historical performance data...")

    with r3_c2:
        st.markdown("<p class='section-title'>RISK VS. REWARD ANALYSIS</p>", unsafe_allow_html=True)
        if not hist_data.empty:
            returns = ((hist_data.iloc[-1] / hist_data.iloc[0]) - 1) * 100
            volatility = hist_data.pct_change().std() * np.sqrt(252) * 100
            scatter_df = pd.DataFrame({'Company': returns.index, 'Return (%)': returns.values, 'Risk (Volatility %)': volatility.values})
            scatter_df = scatter_df.merge(df_market[['Company', 'Market Cap']], on='Company')
            fig_scatter = px.scatter(scatter_df, x='Risk (Volatility %)', y='Return (%)', size='Market Cap', color='Company', text='Company', color_discrete_sequence=AESTHETIC_COLORS)
            fig_scatter.update_traces(textposition='top center', marker=dict(line=dict(width=2, color='rgba(255,255,255,0.5)')))
            fig_scatter.update_layout(template="plotly_dark", paper_bgcolor='rgba(255,255,255,0.03)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, l=10, r=10, b=20), height=350, xaxis_title="Risk (Volatility %)", yaxis_title="Profit/Loss (%)", showlegend=False)
            fig_scatter.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)", opacity=1)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.caption("Fetching risk metrics...")