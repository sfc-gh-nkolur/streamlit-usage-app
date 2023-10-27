# Import python packages
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col
from snowflake.snowpark.window import Window
import plotly.express as px 
import datetime

#############################################
#     FORMATTING
#############################################
#set to wide format
st.set_page_config(layout="wide")

# Write directly to the app
st.title("Snowflake Account Usage App :snowflake:")
st.divider()

#Sub heading info
st.markdown("This app is developed to go off of the account usage schema in your Snowflake account. For detailed information please see the documentation page below.")
st.markdown("https://docs.snowflake.com/en/sql-reference/account-usage#account-usage-views")

#Info bar 
st.info('Developed by Nikhil Kolur & Ashish Patel on the Snowflake Sales Engineering Team. This is not a product of Snowflake please use at your own risk.', icon="ℹ️")
st.divider()

#############################################
#     DATE FILTER
#############################################
max_date = datetime.datetime.now()
min_date = datetime.datetime.now() - datetime.timedelta(days=365)
this_year = max_date.year
jan_1 = datetime.date(this_year, 1, 1)
dec_31 = datetime.date(this_year, 12, 31)


if 'starting' not in st.session_state:
    st.session_state.starting = datetime.datetime.now() - datetime.timedelta(days=30)

if 'ending' not in st.session_state:
    st.session_state.ending = max_date


st.markdown("Enter your desired date range (30 days on initial load):")

#Column for Date Picker Buttons
col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1])

with col1:
    if st.button('30 Days'):
            st.session_state.starting = datetime.datetime.now() - datetime.timedelta(days=30)
            st.session_state.ending = datetime.datetime.now()
with col2:
    if st.button('60 Days'):
            st.session_state.starting = datetime.datetime.now() - datetime.timedelta(days=60)
            st.session_state.ending = datetime.datetime.now()
with col3:
    if st.button('90 Days'):
            st.session_state.starting = datetime.datetime.now() - datetime.timedelta(days=90)
            st.session_state.ending = datetime.datetime.now()
with col4:
    if st.button('180 Days'):
            st.session_state.starting = datetime.datetime.now() - datetime.timedelta(days=180)
            st.session_state.ending = datetime.datetime.now()
with col5:
    if st.button('365 Days'):
            st.session_state.starting = datetime.datetime.now() - datetime.timedelta(days=365)
            st.session_state.ending = datetime.datetime.now()

#Date Input
d = st.date_input(
    "",
    (st.session_state.starting,st.session_state.ending),
    min_date,
    max_date,
)

start,end = d

y = start.strftime("%Y")
m = start.strftime("%m")
day = start.strftime("%d")
y2 = end.strftime("%Y")
m2 = end.strftime("%m")
day2 = end.strftime("%d")
test =start.strftime("%Y%m%d")

#Date filter for SQL Queries
s = (str(y)+"-"+str(m)+'-'+str(day))
e = (str(y2)+"-"+str(m2)+'-'+str(day2))

st.divider()

# Get the current credentials
session = get_active_session()
credits_used_df = session.sql

#############################################
#     Cards at Top
#############################################
#Credits Used Tile
credits_used_sql = f"select round(sum(credits_used),0) as total_credits from snowflake.account_usage.metering_history where start_time between '{s}' and '{e}'"
credits_used_df = session.sql(credits_used_sql)
pandas_credits_used_df = credits_used_df.to_pandas()
#Final Value
credits_used_tile = pandas_credits_used_df.iloc[0].values

# Total # of Jobs Executed
num_jobs_sql = f"select count(*) as number_of_jobs from snowflake.account_usage.query_history where start_time between '{s}' and '{e}'"
num_jobs_df = session.sql(num_jobs_sql)
pandas_num_jobs_df = num_jobs_df.to_pandas()
#Final Value
num_jobs_tile = pandas_num_jobs_df.iloc[0].values

# Current Storage
current_storage_sql = f"select round(avg(storage_bytes + stage_bytes + failsafe_bytes) / power(1024, 4),2) as billable_tb from snowflake.account_usage.storage_usage where USAGE_DATE = current_date() -1;"
current_storage_df = session.sql(current_storage_sql)
pandas_current_storage_df = current_storage_df.to_pandas()
#Final Value
current_storage_tile = pandas_current_storage_df.iloc[0].values

#Column formatting and metrics of header 3 metrics
col1, col2, col3 = st.columns(3)
col1.metric("Credits Used","{:,}".format(int(credits_used_tile))) 
col2.metric("Total # of Jobs Executed","{:,}".format(int(num_jobs_tile))) 
col3.metric("Current Storage (TB)",current_storage_tile)



#############################################
#     Credit Usage Total (Bar Chart)
#############################################

#Credits Usage (Total)
total_credits_used_sql = f"select warehouse_name,sum(credits_used) as total_credits_used from snowflake.account_usage.warehouse_metering_history where start_time between '{s}' and '{e}' group by 1 order by 2 desc limit 10 "
total_credits_used_df = session.sql(total_credits_used_sql)
pandas_credits_used_df = total_credits_used_df.to_pandas()

                                    
#Convert to a pandas df
pandas_total_credits_used_df = total_credits_used_df.to_pandas()

#Chart
fig_credits_used=px.bar(pandas_credits_used_df,x='TOTAL_CREDITS_USED',y='WAREHOUSE_NAME',orientation='h',title="Credits Used by Warehouse")
fig_credits_used.update_traces(marker_color='green')

#############################################
#     Jobs by Warehouse
#############################################

#Jobs by Warehouse Data Setup
jobs_by_warehouse_sql = f"select warehouse_name,count(*) as number_of_jobs from snowflake.account_usage.query_history where start_time between '{s}' and '{e}' group by 1 order by 2 desc limit 10"
jobs_by_warehouse_df = session.sql(jobs_by_warehouse_sql)

#convert to pandas df
pandas_jobs_by_warehouse_df = jobs_by_warehouse_df.to_pandas()

#chart
fig_jobs_by_warehouse=px.bar(pandas_jobs_by_warehouse_df,x='NUMBER_OF_JOBS',y='WAREHOUSE_NAME',orientation='h',title="# of Jobs by Warehouse")
fig_jobs_by_warehouse.update_traces(marker_color='purple')

#############################################
#    Execution by Query Type
#############################################

#Average Execution by Query Type
execution_by_qtype = f"select query_type, warehouse_size, avg(execution_time) / 1000 as average_execution_time from snowflake.account_usage.query_history where start_time between '{s}' and '{e}' group by 1, 2 order by 3 desc;"
execution_by_qtype_df = session.sql(execution_by_qtype)

#convert to pandas df
pandas_execution_by_qtype_df = execution_by_qtype_df.to_pandas()


#chart
fig_execution_by_qtype=px.bar(pandas_execution_by_qtype_df,x='AVERAGE_EXECUTION_TIME',y='QUERY_TYPE',orientation='h',title="Average Execution by Query Type")
#st.write(fig_execution_by_qtype)

#############################################
#     Container 1: Credits & Jobs
#############################################

container1 = st.container()

with container1:
    plot1, plot2,plot3 = st.columns(3)
    with plot1:
        st.plotly_chart(fig_credits_used, use_container_width=True)
    with plot2:
        st.plotly_chart(fig_jobs_by_warehouse, use_container_width=True)
    with plot3:
        st.plotly_chart(fig_execution_by_qtype, use_container_width=True)


#############################################
#     Credits Used Overtime
#############################################

#Credits Used Overtime
credits_used_overtime_sql = f"select start_time::date as usage_date, warehouse_name, sum(credits_used) as total_credits_used from snowflake.account_usage.warehouse_metering_history where start_time between '{s}' and '{e}' group by 1,2 order by 2,1"
credits_used_overtime_df = session.sql(credits_used_overtime_sql)

#convert to pandas df
pandas_credits_used_overtime_df = credits_used_overtime_df.to_pandas()

#chart
fig_credits_used_overtime_df=px.bar(pandas_credits_used_overtime_df,x='USAGE_DATE',y='TOTAL_CREDITS_USED',color='WAREHOUSE_NAME',orientation='v',title="Credits Used Overtime")
st.plotly_chart(fig_credits_used_overtime_df, use_container_width=True)



#############################################
#     Top 25 Longest Queries (Success)
#############################################

#Top 25 Longest Queries (Success)
longest_queries_sql = f"select query_id,query_text,(execution_time / 60000) as exec_time from snowflake.account_usage.query_history where execution_status = 'SUCCESS' and start_time between '{s}' and '{e}' order by execution_time desc limit 25"
longest_queries_df = session.sql(longest_queries_sql)

#convert to pandas df
pandas_longest_queries_df = longest_queries_df.to_pandas()

#chart
fig_longest_queries=px.bar(pandas_longest_queries_df,x='EXEC_TIME',y='QUERY_TEXT',orientation='h',title="Longest Successful Queries (Top 25) ")
#st.write(fig_longest_queries)

#############################################
#     Top 25 Longest Queries (Failed)
#############################################

#Top 25 Longest Queries (Failed)
f_longest_queries_sql = f"select query_id,query_text,(execution_time / 60000) as exec_time from snowflake.account_usage.query_history where execution_status = 'FAIL' and start_time between '{s}' and '{e}' order by execution_time desc limit 25"
f_longest_queries_df = session.sql(longest_queries_sql)


#convert to pandas df
f_pandas_longest_queries_df = longest_queries_df.to_pandas()

#chart
fig_f_longest_queries=px.bar(f_pandas_longest_queries_df,x='EXEC_TIME',y='QUERY_TEXT',orientation='h',title="Longest Failed Queries (Top 25)")
fig_f_longest_queries.update_traces(marker_color='red')
#st.write(fig_f_longest_queries)



#############################################
#     Container 2: Query Success/Failure
#############################################

container2 = st.container()

with container2:
    plot1, plot2 = st.columns(2)
    with plot1:
        st.plotly_chart(fig_longest_queries, use_container_width=True)
    with plot2:
        st.plotly_chart(fig_f_longest_queries, use_container_width=True)

#############################################
#     Warehouse Variance overtime
#############################################

warehouse_variance_sql=f"SELECT WAREHOUSE_NAME, DATE(START_TIME) AS DATE, SUM(CREDITS_USED) AS CREDITS_USED, AVG(SUM(CREDITS_USED)) OVER (PARTITION BY WAREHOUSE_NAME ORDER BY DATE ROWS 7 PRECEDING) AS CREDITS_USED_7_DAY_AVG, (TO_NUMERIC(SUM(CREDITS_USED)/CREDITS_USED_7_DAY_AVG*100,10,2)-100)::STRING || '%' AS VARIANCE_TO_7_DAY_AVERAGE FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY where start_time between '{s}' and '{e}' GROUP BY DATE, WAREHOUSE_NAME ORDER BY DATE DESC"
warehouse_variance_df = session.sql(warehouse_variance_sql)

#convert to pandas
pandas_warehouse_variance_df = warehouse_variance_df.to_pandas()

#chart
fig_warehouse_variance_df=px.bar(pandas_warehouse_variance_df,x="DATE",y="VARIANCE_TO_7_DAY_AVERAGE",color ='WAREHOUSE_NAME',orientation='v',title="Warehouse Variance Greater than 7 day Average")
st.plotly_chart(fig_warehouse_variance_df, use_container_width=True)

#############################################
#     Total Execution Time by Repeated Queries
#############################################

total_execution_time_sql = f"select query_text, (sum(execution_time) / 60000) as exec_time from snowflake.account_usage.query_history where execution_status = 'SUCCESS' and start_time between '{s}' and '{e}' group by query_text order by exec_time desc limit 10"
total_execution_time_df = session.sql(total_execution_time_sql).to_pandas()
#st.write(total_execution_time_df)
fig_execution_time=px.bar(total_execution_time_df,x='EXEC_TIME',y='QUERY_TEXT', orientation='h',title="Total Execution Time by Repeated Queries")
fig_execution_time.update_traces(marker_color='LightSkyBlue')
st.plotly_chart(fig_execution_time, use_container_width=True)


#############################################
#     Credits Billed by Month
#############################################

credits_billed = f"select date_trunc('MONTH', usage_date) as Usage_Month, sum(CREDITS_BILLED) from snowflake.account_usage.metering_daily_history group by Usage_Month"
credits_billed_df = session.sql(credits_billed).to_pandas()
#st.write(credits_billed_df)
fig_credits_billed=px.bar(credits_billed_df,x='USAGE_MONTH',y='SUM(CREDITS_BILLED)', orientation='v',title="Credits Billed by Month")
st.plotly_chart(fig_credits_billed, use_container_width=True)

st.info('The above chart is static and non modified by the date range filter', icon="ℹ️")

#############################################
#  Top 10 Average Query Execution Time (By User)
#############################################

query_execution = "select user_name, (avg(execution_time)) / 1000 as average_execution_time from snowflake.account_usage.query_history group by 1 order by 2 desc limit 10"
query_execution_df = session.sql(query_execution).to_pandas()
#st.write(query_execution_df)
fig_cquery_execution=px.bar(query_execution_df,x='USER_NAME',y='AVERAGE_EXECUTION_TIME', orientation='v',title="Average Execution Time per User")
fig_cquery_execution.update_traces(marker_color='MediumPurple')
st.plotly_chart(fig_cquery_execution,use_container_width=True)


#############################################
#     GS Utilization by Query Type (Top 10)
#############################################

gs_utilization = "select query_type, sum(credits_used_cloud_services) cs_credits, count(1) num_queries from snowflake.account_usage.query_history where true group by 1 order by 2 desc limit 10"
gs_utilization_df = session.sql(gs_utilization).to_pandas()
#st.write(gs_utilization_df)
fig_gs_utilization=px.bar(gs_utilization_df,x='QUERY_TYPE',y='CS_CREDITS', orientation='v',title="GS Utilization by Query Type (Top 10)")
fig_gs_utilization.update_traces(marker_color='red')
#st.plotly_chart(fig_gs_utilization)

#############################################
#     Top 10 Cloud Services by Warehouse                 
#############################################

compute_gs_by_warehouse = "select warehouse_name, sum(credits_used_cloud_services) CREDITS_USED_CLOUD_SERVICES from snowflake.account_usage.warehouse_metering_history where true group by 1 order by 2 desc limit 10"
compute_gs_by_warehouse_df = session.sql(compute_gs_by_warehouse).to_pandas()
#st.write(compute_gs_by_warehouse_df)
fig_compute_gs_by_warehouse=px.bar(compute_gs_by_warehouse_df,x='WAREHOUSE_NAME',y='CREDITS_USED_CLOUD_SERVICES', orientation='v',title="Compute and Cloud Services by Warehouse", barmode="group")
fig_compute_gs_by_warehouse.update_traces(marker_color='purple')
#st.plotly_chart(fig_compute_gs_by_warehouse)

#############################################
#     Container 3: Cloud services
#############################################

container2 = st.container()

with container2:
    plot1, plot2 = st.columns(2)
    with plot1:
        st.plotly_chart(fig_gs_utilization, use_container_width=True)
    with plot2:
        st.plotly_chart(fig_compute_gs_by_warehouse, use_container_width=True)


#############################################
#     Credit Breakdown by Day with Cloud Services Adjustment                FIX THIS
#############################################

credit_breakdown = "select * from snowflake.account_usage.metering_daily_history"
credit_breakdown_df = session.sql(credit_breakdown).to_pandas()
#st.write(credit_breakdown_df)
fig_credit_breakdown=px.bar(credit_breakdown_df,x='USAGE_DATE',y='CREDITS_USED_COMPUTE', orientation='v',title="Credit Breakdown by Day with Cloud Services Adjustment", barmode="group")
#st.plotly_chart(fig_credit_breakdown)


#############################################
#     Data Storage used Overtime                
#############################################

storage_overtime = "select date_trunc(month, usage_date) as usage_month, avg(storage_bytes + stage_bytes + failsafe_bytes) / power(1024, 4) as billable_tb, avg(storage_bytes) / power(1024, 4) as Storage_TB, avg(stage_bytes) / power(1024, 4) as Stage_TB, avg(failsafe_bytes) / power(1024, 4) as Failsafe_TB from snowflake.account_usage.storage_usage group by 1 order by 1"
storage_overtime_df = session.sql(storage_overtime).to_pandas()
#st.write(storage_overtime_df)
fig_storage_overtime=px.bar(storage_overtime_df,x='USAGE_MONTH',y='BILLABLE_TB', orientation='v',title="Data Storage used Overtime", barmode="group")
st.plotly_chart(fig_storage_overtime, use_container_width=True)

st.info('The above chart is static and non modified by the date range filter', icon="ℹ️")

#############################################
#     Rows Loaded Overtime                    FIX THIS
#############################################

#rows_loaded = "SELECT TO_CHAR(TO_DATE(load_history.LAST_LOAD_TIME),'YYYY-MM-DD') AS load_history.last_load_time_date COALESCE(SUM(load_history.ROW_COUNT),0) AS "load_history.total_row_count", FROM SNOWFLAKE.ACCOUNT_USAGE.LOAD_HISTORY AS load_history GROUP BY TO_DATE(load_history.LAST_LOAD_TIME) ORDER BY 1 DESC"
#rows_loaded_df = session.sql(storage_overtime).to_pandas()
#st.write(rows_loaded_df)
#fig_rows_loaded=px.bar(rows_loaded_df,x='USAGE_MONTH',y='BILLABLE_TB', orientation='v',title="Data Storage used Overtime", barmode="group")
#st.plotly_chart(fig_rows_loaded)

#############################################
#     Logins by User               
#############################################

logins = "select user_name, sum(iff(is_success = 'NO', 1, 0)) as Failed, count(*) as Success, sum(iff(is_success = 'NO', 1, 0)) / nullif(count(*), 0) as login_failure_rate from snowflake.account_usage.login_history group by 1 order by 4 desc"
logins_df = session.sql(logins).to_pandas()
#st.write(logins_df)
fig_logins=px.bar(logins_df,x='USER_NAME',y='SUCCESS', orientation='v',title="Logins by User", barmode="group")
fig_logins.update_traces(marker_color='green')
#st.plotly_chart(fig_logins)

#############################################
#     Logins by Client               
#############################################

logins_client = "select reported_client_type as Client, user_name, sum(iff(is_success = 'NO', 1, 0)) as Failed, count(*) as Success, sum(iff(is_success = 'NO', 1, 0)) / nullif(count(*), 0) as login_failure_rate from snowflake.account_usage.login_history group by 1, 2 order by 5 desc"
logins_client_df = session.sql(logins_client).to_pandas()
fig_logins_client=px.bar(logins_client_df,x='CLIENT',y='SUCCESS', orientation='v',title="Logins by Client", barmode="group")
fig_logins_client.update_traces(marker_color='purple')


#############################################
#     Container Users
#############################################

container_users = st.container()

with container_users:
    plot1, plot2 = st.columns(2)
    with plot1:
        st.plotly_chart(fig_logins, use_container_width=True)
    with plot2:
        st.plotly_chart(fig_compute_gs_by_warehouse, use_container_width=True)

        
    
#############################################
#     FOOTER
#############################################    
st.divider()
foot1, foot2, foot3 = st.columns([1,1,1])


with foot1:
    st.markdown("Version 1.0")
with foot2:
    st.markdown("Github Link")
with foot3:
    st.markdown("October 2023")
    

