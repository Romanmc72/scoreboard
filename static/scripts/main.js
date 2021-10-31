Vue.component('Scoreboard', {
    props: ['people'],
    template: `
        <h1>
            <table class="scoreboard">
                <tr>
                    <th>Name</th>
                    <th>Score</th>
                </tr>
                <tr v-for="person in people" v-bind:key=person.name>
                    <td>{{ person.name }}</td>
                    <td>{{ person.score }}</td>
                </tr>
            </table>
        </h1>
    `
}); 

new Vue({
    el: '#root',
    data: {
        people: [],
        name: '',
        score: 0,
        game_code: game_code
    },
    methods: {
        updateScoreboard: function() {
            axios
                .get("/api/scoreboard/" + this.game_code)
                .then((response) => {
                    this.people = response.data;
                })
                .catch(function (error) {
                    console.log("Error !!!:");
                    console.log(error);
                });
            return 0
        },
        addPerson: function() {
            axios
                .post("/api/scoreboard/" + this.game_code + "/score/" + this.name, {'score': this.score})
                .then((response) => {
                    console.log(response.data);
                })
                .then(() => {this.updateScoreboard();})
                .catch(function (error) {
                    console.log("Error !!!:");
                    console.log(error);
                });
            this.name = '';
            this.score = 0;
        },
        removePerson: function() {
            axios
                .delete("/api/scoreboard/" + this.game_code + "/score/" + this.name)
                .then((response) => {
                    console.log(response.data);
                })
                .then(() => {this.updateScoreboard();})
                .catch(function (error) {
                    console.log("Error !!!:");
                    console.log(error);
                });
            this.name = '';
        },
        addToScore: function() {
            axios
                .put("/api/scoreboard/" + this.game_code + "/score/" + this.name, {'score': this.score, 'method': 'add'})
                .then((response) => {
                    console.log(response.data);
                })
                .then(() => {this.updateScoreboard();})
                .catch(function (error) {
                    console.log("Error !!!:");
                    console.log(error);
                });
            this.name = '';
            this.score = 0;
        },
        changeScore: function() {
            axios
                .put("/api/scoreboard/" + this.game_code + "/score/" + this.name, {'score': this.score, 'method': 'replace'})
                .then((response) => {
                    console.log(response.data);
                })
                .then(() => {this.updateScoreboard();})
                .catch(function (error) {
                    console.log("Error !!!:");
                    console.log(error);
                });
            this.name = '';
            this.score = 0;
        },
        eraseScoreboard: function() {
            axios
                .delete("/api/scoreboard/" + this.game_code )
                .then((response) => {
                    this.people = response.data;
                })
                .then(() => {this.updateScoreboard();})
                .catch(function (error) {
                    console.log("Error !!!:");
                    console.log(error);
                });
        },
        clearScoreboard: function() {
            axios
                .put("/api/scoreboard/" + this.game_code, {})
                .then((response) => {
                    this.people = response.data;
                })
                .then(() => {this.updateScoreboard();})
                .catch(function (error) {
                    console.log("Error !!!:");
                    console.log(error);
                });
        }
    },
    mounted: function () {
        this.updateScoreboard();
        setInterval(this.updateScoreboard, 3000);
    }
});
