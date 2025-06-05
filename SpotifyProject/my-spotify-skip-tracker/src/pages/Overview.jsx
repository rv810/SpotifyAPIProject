import { useEffect } from 'react';

export const Overview = () => {
    useEffect(() => {
        fetch("http://localhost:8888/playlists")
            .then((response) => response.json())
            .then((data) => {
                console.log("playlists: ", data)
            })
        .catch((error) => {
            console.error("Error fetching playlists: ", error)
        })
    }, [])

    return (
        <div>Hello</div>
    )
}