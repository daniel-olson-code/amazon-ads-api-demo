'use strict';

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

const profileDisplayName = profile => `${profile.accountInfo.name} ~ ${profile.countryCode} ~ ${profile.accountInfo.type}`

const App = props => {
  const [loaded, setLoaded] = React.useState(false);
  const [profiles, setProfiles] = React.useState([]);

  React.useEffect(() => {
    fetchAPI('profiles')
    .then(data=>{
      console.log('data', data);
      setProfiles(data.profiles)}
    )
    .then(() => setLoaded(true));
  }, []);

  if(!loaded) {
    return <div className="container">
      <p>
        loading...
      </p>
    </div>
  }

  const selectProfile = async profileId => {
    await fetchAPI('select-profile', {profile_id: profileId});
    window.location.reload();
  }

  return <div className="container">
    <h1>Profiles</h1>
    <div style={{width: '50%', height: '50%', overflow: 'scroll'}}>
      <table>
        <tr>
          <th>Display Name</th>
          <th>ID</th>
          <th>Select</th>
        </tr>
        {profiles.map(profile => <tr key={profile.profileId}>
          <td>{profileDisplayName(profile)}</td>
          <td>{profile.profileId}</td>
          <td><button onClick={()=>{selectProfile(profile.profileId)}}>select</button></td>
        </tr>)}
      </table>
    </div>
  </div>
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App/>);