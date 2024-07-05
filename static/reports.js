'use strict';

const dateToString = d => d.getFullYear() + "-" + ("0"+(d.getMonth()+1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);// + " " + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2);

const fetchAPI = async (operation, args) => {
    const response = await fetch('/reports-api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            operation,
            ...args
        })
    });
    return response.json();
}

const isObject = x => typeof x === 'object' && !Array.isArray(x) && x !== null;

const Table = props => {
  const {headers, rows, width='50%', height='50%', replaceRows} = props;

  return <div style={{width: width, height: height, overflow: 'scroll'}}>
    <table>
      <tr>
        {headers.map(h=><th>{h}</th>)}
      </tr>
      {rows.map((row, i) => <tr key={`table-${i}`}>
        {row.map((v, j)=>{
          if(isObject(replaceRows)){
            if(Object.keys(replaceRows).map(v=>v).includes(`${j}`)) {
              const El = replaceRows[`${j}`];
              return <td>{<El row={headers.reduce((a, k, i)=>{a[k] = row[i];return a}, {})}/>}</td>
            }
          }
          return <td>{v}</td>
        })}
      </tr>)}
    </table>
  </div>
}

const App = props => {
  const [availableReports, setAvailableReports] = React.useState([]);
  const [reports, setReports] = React.useState([]);
  const [profileName, setProfileName] = React.useState('');
  const [adTypes, setAdTypes] = React.useState([]);
  const [reportTypes, setReportTypes] = React.useState([]);

  const [adType, setAdType] = React.useState('');
  const [reportType, setReportType] = React.useState('');
  const [startDate, setStartDate] = React.useState(dateToString(new Date()));
  const [endDate, setEndDate] = React.useState(dateToString(new Date()));

  React.useEffect(() => {
    fetchAPI('reports')
    .then(data=>{
      console.log('data', data);
      setReports(data.reports)}
    );
    fetchAPI('available-reports')
    .then(data=>{
      console.log('data', data);
      setAvailableReports(data.reports)}
    );
    fetchAPI('profile-name')
    .then(data=>{
      console.log('data', data);
      setProfileName(data.name)}
    );
    fetchAPI('get-values')
    .then(data=>{
      console.log('data', data);
      setAdTypes(data.ad_types);
      setReportTypes(data.report_types);

      if(data.ad_types.length > 0) setAdType(data.ad_types[0]);
      if(data.report_types.length > 0) setReportType(data.report_types[0]);
    });
  }, []);

  const requestReport = () => {
    if(startDate > endDate || (!startDate || !endDate) || !adType || !reportType) {
      alert('Invalid request. Select better values.')
      return
    }

    fetchAPI('request-report', {
      ad_type: adType,
      report_type: reportType,
      start_date: startDate,
      end_date: endDate
    })
    .then(data=>{
      console.log('data', data);
      setReports(data.reports)}
    );
  }

  return <div>
    <h1>Reports</h1>

    <h3> Account | {profileName} </h3>

    {/* <input type="date" id="start" name="trip-start" value="2018-07-22" min="2018-01-01" max="2018-12-31" /> */}

    <label for="start">Start date:</label>

    <input type="date" id="start" onChange={evt=>setStartDate(`${evt.target.value}`)}/>

    <label for="end">End date:</label>

    <input type="date" id="end" onChange={evt=>setEndDate(`${evt.target.value}`)}/>

    <label for="ad-type">Choose an ad type:</label>
    <select name="ad-type" id="ad-type" onChange={evt=>{if(adTypes.includes(evt.target.value)){setAdType(evt.target.value)}}}>
      {adTypes.map(adType=><option value={adType}>{adType}</option>)}
    </select>

    <label for="report-type">Choose a report type:</label>
    <select name="report-type" id="report-type" onChange={evt=>{if(reportTypes.includes(evt.target.value)){setReportType(evt.target.value)}}}>
      {reportTypes.map(reportType=><option value={reportType}>{reportType}</option>)}
    </select>

    <button className="auth-btn" onClick={requestReport}> Request Reporrt </button>

    {/* <Table headers={['Available Reports']} rows={availableReports.map(val=>[val])} width='50vw' height='50vh'/> */}
      <div style={{margin: 50}}></div>
    {reports.length === 0 ? null : 
      <Table 
        width='100vw' 
        height='50vh'
        headers={Object.keys(reports[0]).map(k=>k).concat(['Check Status'])} 
        rows={reports.map(row=>Object.keys(reports[0]).map(k=>k in row ? row[k] : '').concat(['']))} 
        replaceRows={{[`${Object.keys(reports[0]).map(k=>k).length}`]: props=>{const {row} = props; return <button onClick={()=>{
          fetchAPI('report-status', {report_id: row['Report Id']})
          .then(data=>{
            console.log('data', data);
            setReports(data.reports)}
          );
        
        }}>Check</button>;}}}
      />}

  </div>;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App/>);