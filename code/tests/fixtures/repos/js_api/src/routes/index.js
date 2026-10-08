const express = require('express');
import { UserRepo } from '../lib/users';
const app = express();
app.get('/users', (req, res) => res.json(new UserRepo().find()));
